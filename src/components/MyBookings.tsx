import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { useAuth } from '../contexts/AuthContext'
import { Calendar, Clock, Building2, FileText, User } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface Booking {
  id: string
  laboratorio_id: string
  data_agendamento: string
  aulas: number[]
  descricao: string
  status: string
  lab_name?: string
}

const MyBookings: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(true)
  const { supabase } = useSupabase()
  const { user } = useAuth()

  useEffect(() => {
    fetchMyBookings()
  }, [])

  const fetchMyBookings = async () => {
    try {
      const { data: bookingsData, error } = await supabase
        .from('agendamentos')
        .select('*')
        .eq('usuario_id', user?.id)
        .order('data_agendamento', { ascending: false })

      if (error) throw error

      // Enrich bookings with lab names
      const enrichedBookings = await Promise.all(
        (bookingsData || []).map(async (booking) => {
          const { data: labData } = await supabase
            .from('laboratorios')
            .select('nome')
            .eq('id', booking.laboratorio_id)
            .single()

          return {
            ...booking,
            lab_name: labData?.nome
          }
        })
      )

      setBookings(enrichedBookings)
    } catch (error) {
      console.error('Error fetching bookings:', error)
      toast.error('Erro ao carregar seus agendamentos')
    } finally {
      setLoading(false)
    }
  }

  const formatClassNumbers = (classes: number[]) => {
    return classes.sort((a, b) => a - b).map(c => `${c}ª Aula`).join(', ')
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'aprovado':
        return <span className="badge-success">Aprovado</span>
      case 'rejeitado':
        return <span className="badge-error">Rejeitado</span>
      case 'pendente':
        return <span className="badge-warning">Pendente</span>
      default:
        return <span className="badge-primary">{status}</span>
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'aprovado':
        return 'border-green-400'
      case 'rejeitado':
        return 'border-red-400'
      case 'pendente':
        return 'border-yellow-400'
      default:
        return 'border-gray-400'
    }
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Meus Agendamentos</h2>
        <p className="text-gray-600">Visualize o status dos seus agendamentos</p>
      </div>

      {bookings.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Você não possui agendamentos</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-xl font-semibold text-gray-900">{bookings.length}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Pendentes</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {bookings.filter(b => b.status === 'pendente').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Aprovados</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {bookings.filter(b => b.status === 'aprovado').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Rejeitados</p>
                  <p className="text-xl font-semibold text-gray-900">
                    {bookings.filter(b => b.status === 'rejeitado').length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Bookings List */}
          <div className="space-y-4">
            {bookings.map((booking) => (
              <div key={booking.id} className={`bg-white rounded-lg shadow-md p-6 border-l-4 ${getStatusColor(booking.status)}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <Building2 className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{booking.lab_name}</h4>
                        <p className="text-sm text-gray-600">
                          {format(new Date(booking.data_agendamento), 'dd/MM/yyyy', { locale: ptBR })}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                      <div className="flex items-center gap-2 text-sm">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">Aulas:</span>
                        <span className="font-medium">
                          {formatClassNumbers(booking.aulas)}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-600">Status:</span>
                        {getStatusBadge(booking.status)}
                      </div>
                    </div>

                    {booking.descricao && (
                      <div className="flex items-start gap-2 text-sm">
                        <FileText className="w-4 h-4 text-gray-400 mt-0.5" />
                        <div>
                          <span className="text-gray-600">Descrição:</span>
                          <p className="text-gray-900 mt-1">{booking.descricao}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default MyBookings