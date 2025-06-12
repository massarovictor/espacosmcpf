import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { Calendar, Building2, Clock, User, FileText } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import toast from 'react-hot-toast'
import { format, addDays, startOfWeek, endOfWeek } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface Lab {
  id: string
  nome: string
}

interface ScheduleItem {
  type: 'fixed' | 'booking'
  aulas: number[]
  descricao: string
  professor_email?: string
  professor_name?: string
}

interface DaySchedule {
  [date: string]: ScheduleItem[]
}

const DAYS_OF_WEEK = [
  'Segunda-feira',
  'Terça-feira', 
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira'
]

const LabSchedule: React.FC = () => {
  const [labs, setLabs] = useState<Lab[]>([])
  const [selectedLabId, setSelectedLabId] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [schedule, setSchedule] = useState<DaySchedule>({})
  const [loading, setLoading] = useState(true)
  const [loadingSchedule, setLoadingSchedule] = useState(false)
  const { supabase } = useSupabase()

  useEffect(() => {
    fetchLabs()
    setDefaultDates()
  }, [])

  const setDefaultDates = () => {
    const today = new Date()
    const weekStart = startOfWeek(today, { weekStartsOn: 1 }) // Monday
    const weekEnd = endOfWeek(today, { weekStartsOn: 1 }) // Sunday
    
    setStartDate(format(weekStart, 'yyyy-MM-dd'))
    setEndDate(format(weekEnd, 'yyyy-MM-dd'))
  }

  const fetchLabs = async () => {
    try {
      const { data, error } = await supabase
        .from('laboratorios')
        .select('id, nome')
        .order('nome')

      if (error) throw error
      setLabs(data || [])
      
      if (data && data.length > 0) {
        setSelectedLabId(data[0].id)
      }
    } catch (error) {
      console.error('Error fetching labs:', error)
      toast.error('Erro ao carregar laboratórios')
    } finally {
      setLoading(false)
    }
  }

  const fetchSchedule = async () => {
    if (!selectedLabId || !startDate || !endDate) return

    if (new Date(startDate) > new Date(endDate)) {
      toast.error('A data de início não pode ser posterior à data de fim')
      return
    }

    setLoadingSchedule(true)

    try {
      const dates = []
      const current = new Date(startDate)
      const end = new Date(endDate)

      while (current <= end) {
        dates.push(new Date(current))
        current.setDate(current.getDate() + 1)
      }

      const newSchedule: DaySchedule = {}

      // Initialize all dates
      dates.forEach(date => {
        const dateStr = format(date, 'yyyy-MM-dd')
        newSchedule[dateStr] = []
      })

      // Fetch fixed schedules
      const { data: fixedSchedules, error: fixedError } = await supabase
        .from('horarios_fixos')
        .select('*')
        .eq('laboratorio_id', selectedLabId)

      if (fixedError) throw fixedError

      // Add fixed schedules to appropriate dates
      fixedSchedules?.forEach(schedule => {
        dates.forEach(date => {
          const dateStr = format(date, 'yyyy-MM-dd')
          const dayOfWeek = date.getDay() - 1 // Convert to 0-6 (Monday-Sunday)
          
          if (dayOfWeek === schedule.dia_semana &&
              date >= new Date(schedule.data_inicio) &&
              date <= new Date(schedule.data_fim)) {
            newSchedule[dateStr].push({
              type: 'fixed',
              aulas: schedule.aulas,
              descricao: schedule.descricao || 'Horário fixo'
            })
          }
        })
      })

      // Fetch approved bookings
      const { data: bookings, error: bookingsError } = await supabase
        .from('agendamentos')
        .select('*')
        .eq('laboratorio_id', selectedLabId)
        .eq('status', 'aprovado')
        .gte('data_agendamento', startDate)
        .lte('data_agendamento', endDate)

      if (bookingsError) throw bookingsError

      // Add bookings with professor info
      for (const booking of bookings || []) {
        const { data: professorData } = await supabase
          .from('users')
          .select('name, email')
          .eq('id', booking.usuario_id)
          .single()

        newSchedule[booking.data_agendamento].push({
          type: 'booking',
          aulas: booking.aulas,
          descricao: booking.descricao || 'Agendamento',
          professor_email: professorData?.email,
          professor_name: professorData?.name
        })
      }

      setSchedule(newSchedule)
    } catch (error) {
      console.error('Error fetching schedule:', error)
      toast.error('Erro ao carregar agenda')
    } finally {
      setLoadingSchedule(false)
    }
  }

  const formatClassNumbers = (classes: number[]) => {
    return classes.sort((a, b) => a - b).map(c => `${c}ª Aula`).join(', ')
  }

  const getDayName = (dateStr: string) => {
    const date = new Date(dateStr)
    const dayOfWeek = date.getDay()
    return dayOfWeek >= 1 && dayOfWeek <= 5 ? DAYS_OF_WEEK[dayOfWeek - 1] : null
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Agenda dos Espaços</h2>
        <p className="text-gray-600">Visualize a disponibilidade dos laboratórios</p>
      </div>

      {labs.length === 0 ? (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Nenhum laboratório disponível</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Filters */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Escolha o Laboratório
                </label>
                <select
                  value={selectedLabId}
                  onChange={(e) => setSelectedLabId(e.target.value)}
                  className="input-field"
                >
                  {labs.map((lab) => (
                    <option key={lab.id} value={lab.id}>
                      {lab.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Início
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="input-field"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Data Fim
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="input-field"
                />
              </div>
            </div>

            <div className="mt-4">
              <button
                onClick={fetchSchedule}
                disabled={loadingSchedule}
                className="btn-primary flex items-center gap-2"
              >
                {loadingSchedule ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Carregando...
                  </>
                ) : (
                  <>
                    <Calendar className="w-4 h-4" />
                    Consultar Agenda
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Schedule Display */}
          {Object.keys(schedule).length > 0 && (
            <div className="space-y-6">
              {Object.entries(schedule)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([dateStr, items]) => {
                  const dayName = getDayName(dateStr)
                  
                  return (
                    <div key={dateStr} className="bg-white rounded-lg shadow-md p-6">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                          <Calendar className="w-5 h-5 text-primary-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {format(new Date(dateStr), 'dd/MM/yyyy')}
                          </h3>
                          {dayName && (
                            <p className="text-sm text-gray-600">{dayName}</p>
                          )}
                        </div>
                      </div>

                      {items.length === 0 ? (
                        <p className="text-gray-500 text-center py-8">
                          Não há horários fixos ou agendamentos para esta data
                        </p>
                      ) : (
                        <div className="space-y-4">
                          {/* Fixed Schedules */}
                          {items.filter(item => item.type === 'fixed').length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                Horários Fixos
                              </h4>
                              <div className="space-y-2">
                                {items
                                  .filter(item => item.type === 'fixed')
                                  .map((item, index) => (
                                    <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                      <div className="flex items-center justify-between">
                                        <div>
                                          <p className="font-medium text-blue-900">
                                            {formatClassNumbers(item.aulas)}
                                          </p>
                                          <p className="text-sm text-blue-700">{item.descricao}</p>
                                        </div>
                                        <span className="badge-primary">Fixo</span>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}

                          {/* Approved Bookings */}
                          {items.filter(item => item.type === 'booking').length > 0 && (
                            <div>
                              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                                <User className="w-4 h-4" />
                                Agendamentos Aprovados
                              </h4>
                              <div className="space-y-2">
                                {items
                                  .filter(item => item.type === 'booking')
                                  .map((item, index) => (
                                    <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                                      <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                          <div className="flex items-center gap-2 mb-1">
                                            <p className="font-medium text-green-900">
                                              {formatClassNumbers(item.aulas)}
                                            </p>
                                            <span className="badge-success">Aprovado</span>
                                          </div>
                                          <p className="text-sm text-green-700 mb-1">
                                            Professor: {item.professor_name || item.professor_email}
                                          </p>
                                          <p className="text-sm text-green-600">{item.descricao}</p>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LabSchedule