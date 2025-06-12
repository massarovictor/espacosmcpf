import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { useAuth } from '../contexts/AuthContext'
import { Calendar, Plus, Edit, Trash2, Clock } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import Modal from './Modal'
import ConfirmDialog from './ConfirmDialog'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

interface FixedSchedule {
  id: string
  laboratorio_id: string
  dia_semana: number
  aulas: number[]
  data_inicio: string
  data_fim: string
  descricao: string
  lab_name?: string
}

interface Lab {
  id: string
  nome: string
}

interface ScheduleFormData {
  laboratorio_id: string
  dia_semana: number
  aulas: number[]
  data_inicio: string
  data_fim: string
  descricao: string
}

const DAYS_OF_WEEK = [
  { value: 0, label: 'Segunda-feira' },
  { value: 1, label: 'Terça-feira' },
  { value: 2, label: 'Quarta-feira' },
  { value: 3, label: 'Quinta-feira' },
  { value: 4, label: 'Sexta-feira' }
]

const CLASS_OPTIONS = Array.from({ length: 9 }, (_, i) => i + 1)

const FixedSchedules: React.FC = () => {
  const [schedules, setSchedules] = useState<FixedSchedule[]>([])
  const [labs, setLabs] = useState<Lab[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedSchedule, setSelectedSchedule] = useState<FixedSchedule | null>(null)
  const [formData, setFormData] = useState<ScheduleFormData>({
    laboratorio_id: '',
    dia_semana: 0,
    aulas: [],
    data_inicio: '',
    data_fim: '',
    descricao: ''
  })
  const { supabase } = useSupabase()
  const { user } = useAuth()

  useEffect(() => {
    fetchLabsAndSchedules()
  }, [])

  const fetchLabsAndSchedules = async () => {
    try {
      // Get labs managed by this admin
      const { data: labsData, error: labsError } = await supabase
        .from('laboratorios')
        .select('id, nome')
        .eq('administrador_id', user?.id)

      if (labsError) throw labsError

      setLabs(labsData || [])

      if (!labsData || labsData.length === 0) {
        setSchedules([])
        setLoading(false)
        return
      }

      const labIds = labsData.map(lab => lab.id)

      // Get fixed schedules for these labs
      const { data: schedulesData, error: schedulesError } = await supabase
        .from('horarios_fixos')
        .select('*')
        .in('laboratorio_id', labIds)
        .order('dia_semana')

      if (schedulesError) throw schedulesError

      // Enrich schedules with lab names
      const enrichedSchedules = (schedulesData || []).map(schedule => ({
        ...schedule,
        lab_name: labsData.find(lab => lab.id === schedule.laboratorio_id)?.nome
      }))

      setSchedules(enrichedSchedules)
    } catch (error) {
      console.error('Error fetching schedules:', error)
      toast.error('Erro ao carregar horários fixos')
    } finally {
      setLoading(false)
    }
  }

  const handleAddSchedule = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.laboratorio_id) {
      toast.error('Selecione um laboratório')
      return
    }

    if (formData.aulas.length === 0) {
      toast.error('Selecione pelo menos uma aula')
      return
    }

    if (new Date(formData.data_inicio) > new Date(formData.data_fim)) {
      toast.error('A data de início não pode ser posterior à data de fim')
      return
    }

    try {
      const { error } = await supabase
        .from('horarios_fixos')
        .insert({
          laboratorio_id: formData.laboratorio_id,
          dia_semana: formData.dia_semana,
          aulas: formData.aulas,
          data_inicio: formData.data_inicio,
          data_fim: formData.data_fim,
          descricao: formData.descricao.trim()
        })

      if (error) throw error

      toast.success('Horário fixo adicionado com sucesso!')
      setShowAddModal(false)
      resetForm()
      fetchLabsAndSchedules()
    } catch (error) {
      console.error('Error adding schedule:', error)
      toast.error('Erro ao adicionar horário fixo')
    }
  }

  const handleEditSchedule = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedSchedule) return

    if (formData.aulas.length === 0) {
      toast.error('Selecione pelo menos uma aula')
      return
    }

    if (new Date(formData.data_inicio) > new Date(formData.data_fim)) {
      toast.error('A data de início não pode ser posterior à data de fim')
      return
    }

    try {
      const { error } = await supabase
        .from('horarios_fixos')
        .update({
          dia_semana: formData.dia_semana,
          aulas: formData.aulas,
          data_inicio: formData.data_inicio,
          data_fim: formData.data_fim,
          descricao: formData.descricao.trim()
        })
        .eq('id', selectedSchedule.id)

      if (error) throw error

      toast.success('Horário fixo atualizado com sucesso!')
      setShowEditModal(false)
      resetForm()
      fetchLabsAndSchedules()
    } catch (error) {
      console.error('Error updating schedule:', error)
      toast.error('Erro ao atualizar horário fixo')
    }
  }

  const handleDeleteSchedule = async () => {
    if (!selectedSchedule) return

    try {
      const { error } = await supabase
        .from('horarios_fixos')
        .delete()
        .eq('id', selectedSchedule.id)

      if (error) throw error

      toast.success('Horário fixo excluído com sucesso!')
      setShowDeleteDialog(false)
      setSelectedSchedule(null)
      fetchLabsAndSchedules()
    } catch (error) {
      console.error('Error deleting schedule:', error)
      toast.error('Erro ao excluir horário fixo')
    }
  }

  const resetForm = () => {
    setFormData({
      laboratorio_id: '',
      dia_semana: 0,
      aulas: [],
      data_inicio: '',
      data_fim: '',
      descricao: ''
    })
    setSelectedSchedule(null)
  }

  const openEditModal = (schedule: FixedSchedule) => {
    setSelectedSchedule(schedule)
    setFormData({
      laboratorio_id: schedule.laboratorio_id,
      dia_semana: schedule.dia_semana,
      aulas: schedule.aulas,
      data_inicio: schedule.data_inicio,
      data_fim: schedule.data_fim,
      descricao: schedule.descricao || ''
    })
    setShowEditModal(true)
  }

  const openDeleteDialog = (schedule: FixedSchedule) => {
    setSelectedSchedule(schedule)
    setShowDeleteDialog(true)
  }

  const formatClassNumbers = (classes: number[]) => {
    return classes.sort((a, b) => a - b).map(c => `${c}ª Aula`).join(', ')
  }

  const getDayName = (dayNumber: number) => {
    return DAYS_OF_WEEK.find(day => day.value === dayNumber)?.label || 'Desconhecido'
  }

  const handleClassToggle = (classNumber: number) => {
    setFormData(prev => ({
      ...prev,
      aulas: prev.aulas.includes(classNumber)
        ? prev.aulas.filter(c => c !== classNumber)
        : [...prev.aulas, classNumber].sort((a, b) => a - b)
    }))
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Gerenciar Horários Fixos</h3>
        {labs.length > 0 && (
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Adicionar Horário
          </button>
        )}
      </div>

      {labs.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Você não está associado a nenhum laboratório</p>
        </div>
      ) : schedules.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Nenhum horário fixo cadastrado</p>
        </div>
      ) : (
        <div className="space-y-4">
          {schedules.map((schedule) => (
            <div key={schedule.id} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                      <Calendar className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">
                        {getDayName(schedule.dia_semana)} - {schedule.lab_name}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {formatClassNumbers(schedule.aulas)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div className="text-sm">
                      <span className="text-gray-600">Período:</span>
                      <span className="ml-2 font-medium">
                        {format(new Date(schedule.data_inicio), 'dd/MM/yyyy')} até{' '}
                        {format(new Date(schedule.data_fim), 'dd/MM/yyyy')}
                      </span>
                    </div>
                  </div>

                  {schedule.descricao && (
                    <div className="text-sm">
                      <span className="text-gray-600">Descrição:</span>
                      <p className="text-gray-900 mt-1">{schedule.descricao}</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => openEditModal(schedule)}
                    className="text-primary-600 hover:text-primary-900 p-2 rounded-md hover:bg-primary-50"
                    title="Editar horário"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openDeleteDialog(schedule)}
                    className="text-red-600 hover:text-red-900 p-2 rounded-md hover:bg-red-50"
                    title="Excluir horário"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Schedule Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false)
          resetForm()
        }}
        title="Adicionar Novo Horário Fixo"
      >
        <form onSubmit={handleAddSchedule} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Laboratório *
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
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dia da Semana *
              </label>
              <select
                value={formData.dia_semana}
                onChange={(e) => setFormData({ ...formData, dia_semana: parseInt(e.target.value) })}
                className="input-field"
                required
              >
                {DAYS_OF_WEEK.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Aulas *
            </label>
            <div className="grid grid-cols-3 gap-2">
              {CLASS_OPTIONS.map((classNumber) => (
                <label key={classNumber} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.aulas.includes(classNumber)}
                    onChange={() => handleClassToggle(classNumber)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">{classNumber}ª Aula</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data de Início *
              </label>
              <input
                type="date"
                value={formData.data_inicio}
                onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data de Fim *
              </label>
              <input
                type="date"
                value={formData.data_fim}
                onChange={(e) => setFormData({ ...formData, data_fim: e.target.value })}
                className="input-field"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição
            </label>
            <textarea
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              className="input-field"
              placeholder="Descrição opcional"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => {
                setShowAddModal(false)
                resetForm()
              }}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button type="submit" className="btn-primary">
              Adicionar Horário
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Schedule Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          resetForm()
        }}
        title="Editar Horário Fixo"
      >
        <form onSubmit={handleEditSchedule} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Laboratório
            </label>
            <input
              type="text"
              value={selectedSchedule?.lab_name || ''}
              className="input-field bg-gray-50"
              disabled
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dia da Semana *
            </label>
            <select
              value={formData.dia_semana}
              onChange={(e) => setFormData({ ...formData, dia_semana: parseInt(e.target.value) })}
              className="input-field"
              required
            >
              {DAYS_OF_WEEK.map((day) => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Aulas *
            </label>
            <div className="grid grid-cols-3 gap-2">
              {CLASS_OPTIONS.map((classNumber) => (
                <label key={classNumber} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.aulas.includes(classNumber)}
                    onChange={() => handleClassToggle(classNumber)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">{classNumber}ª Aula</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data de Início *
              </label>
              <input
                type="date"
                value={formData.data_inicio}
                onChange={(e) => setFormData({ ...formData, data_inicio: e.target.value })}
                className="input-field"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data de Fim *
              </label>
              <input
                type="date"
                value={formData.data_fim}
                onChange={(e) => setFormData({ ...formData, data_fim: e.target.value })}
                className="input-field"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição
            </label>
            <textarea
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              className="input-field"
              placeholder="Descrição opcional"
              rows={3}
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => {
                setShowEditModal(false)
                resetForm()
              }}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button type="submit" className="btn-primary">
              Atualizar Horário
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setSelectedSchedule(null)
        }}
        onConfirm={handleDeleteSchedule}
        title="Excluir Horário Fixo"
        message={`Tem certeza que deseja excluir este horário fixo? Esta ação não pode ser desfeita.`}
        confirmText="Excluir"
        confirmButtonClass="btn-danger"
      />
    </div>
  )
}

export default FixedSchedules