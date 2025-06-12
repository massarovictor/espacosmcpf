import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { useAuth } from '../contexts/AuthContext'
import { Calendar, Clock, Building2, FileText } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import toast from 'react-hot-toast'
import { format, addDays } from 'date-fns'

interface Lab {
  id: string
  nome: string
  descricao: string
  capacidade: number
}

interface BookingFormData {
  laboratorio_id: string
  data_agendamento: string
  aulas: number[]
  descricao: string
}

const CLASS_OPTIONS = Array.from({ length: 9 }, (_, i) => i + 1)

const BookLab: React.FC = () => {
  const [labs, setLabs] = useState<Lab[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState<BookingFormData>({
    laboratorio_id: '',
    data_agendamento: '',
    aulas: [],
    descricao: ''
  })
  const { supabase } = useSupabase()
  const { user } = useAuth()

  useEffect(() => {
    fetchLabs()
  }, [])

  const fetchLabs = async () => {
    try {
      const { data, error } = await supabase
        .from('laboratorios')
        .select('*')
        .order('nome')

      if (error) throw error
      setLabs(data || [])
    } catch (error) {
      console.error('Error fetching labs:', error)
      toast.error('Erro ao carregar laboratórios')
    } finally {
      setLoading(false)
    }
  }

  const checkAvailability = async (labId: string, date: string, classes: number[]) => {
    try {
      const dayOfWeek = new Date(date).getDay() - 1 // Convert to 0-6 (Monday-Sunday)
      
      // Check fixed schedules
      const { data: fixedSchedules, error: fixedError } = await supabase
        .from('horarios_fixos')
        .select('*')
        .eq('laboratorio_id', labId)
        .eq('dia_semana', dayOfWeek)
        .lte('data_inicio', date)
        .gte('data_fim', date)

      if (fixedError) throw fixedError

      const unavailableClasses = new Set<number>()

      // Add classes from fixed schedules
      fixedSchedules?.forEach(schedule => {
        schedule.aulas.forEach((aula: number) => unavailableClasses.add(aula))
      })

      // Check existing approved bookings
      const { data: bookings, error: bookingsError } = await supabase
        .from('agendamentos')
        .select('aulas')
        .eq('laboratorio_id', labId)
        .eq('data_agendamento', date)
        .eq('status', 'aprovado')

      if (bookingsError) throw bookingsError

      // Add classes from existing bookings
      bookings?.forEach(booking => {
        booking.aulas.forEach((aula: number) => unavailableClasses.add(aula))
      })

      // Check for conflicts
      const conflicts = classes.filter(cls => unavailableClasses.has(cls))
      return { available: conflicts.length === 0, conflicts }
    } catch (error) {
      console.error('Error checking availability:', error)
      return { available: false, conflicts: [] }
    }
  }

  const checkDuplicateBooking = async (labId: string, date: string, classes: number[]) => {
    try {
      const { data, error } = await supabase
        .from('agendamentos')
        .select('id')
        .eq('usuario_id', user?.id)
        .eq('laboratorio_id', labId)
        .eq('data_agendamento', date)
        .eq('status', 'pendente')
        .contains('aulas', classes)

      if (error) throw error
      return data && data.length > 0
    } catch (error) {
      console.error('Error checking duplicate booking:', error)
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.laboratorio_id) {
      toast.error('Selecione um laboratório')
      return
    }

    if (formData.aulas.length === 0) {
      toast.error('Selecione pelo menos uma aula')
      return
    }

    if (!formData.descricao.trim()) {
      toast.error('Descrição da atividade é obrigatória')
      return
    }

    setSubmitting(true)

    try {
      // Check for duplicate booking
      const isDuplicate = await checkDuplicateBooking(
        formData.laboratorio_id,
        formData.data_agendamento,
        formData.aulas
      )

      if (isDuplicate) {
        toast.error('Você já requisitou esse agendamento. Espere a revisão do administrador.')
        return
      }

      // Check availability
      const { available, conflicts } = await checkAvailability(
        formData.laboratorio_id,
        formData.data_agendamento,
        formData.aulas
      )

      if (!available) {
        const conflictClasses = conflicts.map(c => `${c}ª Aula`).join(', ')
        toast.error(`O laboratório não está disponível nas seguintes aulas: ${conflictClasses}`)
        return
      }

      // Create booking
      const { error } = await supabase
        .from('agendamentos')
        .insert({
          usuario_id: user?.id,
          laboratorio_id: formData.laboratorio_id,
          data_agendamento: formData.data_agendamento,
          aulas: formData.aulas,
          descricao: formData.descricao.trim(),
          status: 'pendente'
        })

      if (error) throw error

      toast.success('Agendamento solicitado com sucesso! Aguardando aprovação.')
      
      // Reset form
      setFormData({
        laboratorio_id: '',
        data_agendamento: '',
        aulas: [],
        descricao: ''
      })

    } catch (error) {
      console.error('Error creating booking:', error)
      toast.error('Erro ao criar agendamento')
    } finally {
      setSubmitting(false)
    }
  }

  const handleClassToggle = (classNumber: number) => {
    setFormData(prev => ({
      ...prev,
      aulas: prev.aulas.includes(classNumber)
        ? prev.aulas.filter(c => c !== classNumber)
        : [...prev.aulas, classNumber].sort((a, b) => a - b)
    }))
  }

  const getMinDate = () => {
    return format(new Date(), 'yyyy-MM-dd')
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Agendar Espaço</h2>
        <p className="text-gray-600">Solicite o agendamento de um laboratório</p>
      </div>

      {labs.length === 0 ? (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Nenhum laboratório disponível</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Escolha o Laboratório *
              </label>
              <select
                value={formData.laboratorio_id}
                onChange={(e) => setFormData({ ...formData, laboratorio_id: e.target.value })}
                className="input-field"
                required
              >
                <option value="">Selecione um laboratório</option>
                {labs.map((lab) => (
                  <option key={lab.id} value={lab.id}>
                    {lab.nome}
                    {lab.capacidade > 0 && ` (Capacidade: ${lab.capacidade})`}
                  </option>
                ))}
              </select>
              
              {formData.laboratorio_id && (
                <div className="mt-2 p-3 bg-gray-50 rounded-md">
                  {(() => {
                    const selectedLab = labs.find(lab => lab.id === formData.laboratorio_id)
                    return selectedLab?.descricao ? (
                      <p className="text-sm text-gray-600">{selectedLab.descricao}</p>
                    ) : null
                  })()}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data do Agendamento *
              </label>
              <input
                type="date"
                value={formData.data_agendamento}
                onChange={(e) => setFormData({ ...formData, data_agendamento: e.target.value })}
                className="input-field"
                min={getMinDate()}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Selecione as Aulas *
              </label>
              <div className="grid grid-cols-3 gap-3">
                {CLASS_OPTIONS.map((classNumber) => (
                  <label key={classNumber} className="flex items-center gap-2 cursor-pointer p-2 rounded-md hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={formData.aulas.includes(classNumber)}
                      onChange={() => handleClassToggle(classNumber)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm font-medium">{classNumber}ª Aula</span>
                  </label>
                ))}
              </div>
              {formData.aulas.length > 0 && (
                <div className="mt-2 p-2 bg-primary-50 rounded-md">
                  <p className="text-sm text-primary-800">
                    Aulas selecionadas: {formData.aulas.map(c => `${c}ª`).join(', ')}
                  </p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descrição da Atividade *
              </label>
              <textarea
                value={formData.descricao}
                onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                className="input-field"
                placeholder="Descreva brevemente a atividade que será realizada no laboratório"
                rows={4}
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                Forneça detalhes sobre o que será feito durante o agendamento
              </p>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="btn-primary flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processando...
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4" />
                    Confirmar Agendamento
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default BookLab