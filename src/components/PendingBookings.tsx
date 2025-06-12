import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { useAuth } from '../contexts/AuthContext'
import { Clock, User, Calendar, FileText, Check, X } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface PendingBooking {
  id: string
  usuario_id: string
  laboratorio_id: string
  data_agendamento: string
  aulas: number[]
  descricao: string
  status: string
  professor_name?: string
  professor_email?: string
  lab_name?: string
}

const PendingBookings: React.FC = () => {
  const [bookings, setBookings] = useState<PendingBooking[]>([])
  const [loading, setLoading] = useState(true)
  const { supabase } = useSupabase()
  const { user } = useAuth()

  useEffect(() => {
    fetchPendingBookings()
  }, [])

  const fetchPendingBookings = async () => {
    try {
      // First, get labs managed by this admin
      const { data: labs, error: labsError } = await supabase
        .from('laboratorios')
        .select('id')
        .eq('administrador_id', user?.id)

      if (labsError) throw labsError

      if (!labs || labs.length === 0) {
        setBookings([])
        setLoading(false)
        return
      }

      const labIds = labs.map(lab => lab.id)

      // Get pending bookings for these labs
      const { data: bookingsData, error: bookingsError } = await supabase
        .from('agendamentos')
        .select('*')
        .in('laboratorio_id', labIds)
        .eq('status', 'pendente')
        .order('data_agendamento', { ascending: true })

      if (bookingsError) throw bookingsError

      // Enrich bookings with professor and lab info
      const enrichedBookings = await Promise.all(
        (bookingsData || []).map(async (booking) => {
          // Get professor info
          const { data: professorData } = await supabase
            .from('users')
            .select('name, email')
            .eq('id', booking.usuario_id)
            .single()

          // Get lab info
          const { data: labData } = await supabase
            .from('laboratorios')
            .select('nome')
            .eq('id', booking.laboratorio_id)
            .single()

          return {
            ...booking,
            professor_name: professorData?.name,
            professor_email: professorData?.email,
            lab_name: labData?.nome
          }
        })
      )

      setBookings(enrichedBookings)
    } catch (error) {
      console.error('Error fetching pending bookings:', error)
      toast.error('Erro ao carregar agendamentos pendentes')
    } finally {
      setLoading(false)
    }
  }

  const updateBookingStatus = async (bookingId: string, newStatus: 'aprovado' | 'rejeitado') => {
    try {
      const { error } = await supabase
        .from('agendamentos')
        .update({ status: newStatus })
        .eq('id', bookingId)

      if (error) throw error

      // Get booking details for email notification
      const booking = bookings.find(b => b.id === bookingId)
      if (booking) {
        await sendEmailNotification(booking, newStatus)
      }

      toast.success(`Agendamento ${newStatus} com sucesso!`)
      fetchPendingBookings() // Refresh the list
    } catch (error) {
      console.error('Error updating booking status:', error)
      toast.error('Erro ao atualizar status do agendamento')
    }
  }

  const sendEmailNotification = async (booking: PendingBooking, status: string) => {
    // This would integrate with your email service
    // For now, we'll just log it
    console.log('Email notification would be sent:', {
      to: booking.professor_email,
      subject: `Agendamento ${status.charAt(0).toUpperCase() + status.slice(1)}`,
      booking: booking
    })
  }

  const formatClassNumbers = (classes: number[]) => {
    return classes.sort((a, b) => a - b).map(c => `${c}ª Aula`).join(', ')
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Agendamentos Pendentes</h3>

      {bookings.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Nenhum agendamento pendente</p>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <div key={booking.id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-400">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">
                        {booking.professor_name || 'Sem nome'}
                      </h4>
                      <p className="text-sm text-gray-600">{booking.professor_email}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-600">Data:</span>
                      <span className="font-medium">
                        {format(new Date(booking.data_agendamento), 'dd/MM/yyyy')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-600">Aulas:</span>
                      <span className="font-medium">
                        {formatClassNumbers(booking.aulas)}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600">Laboratório:</span>
                      <span className="font-medium">{booking.lab_name}</span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <span className="badge-warning">Pendente</span>
                    </div>
                  </div>

                  {booking.descricao && (
                    <div className="flex items-start gap-2 text-sm mb-4">
                      <FileText className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div>
                        <span className="text-gray-600">Descrição:</span>
                        <p className="text-gray-900 mt-1">{booking.descricao}</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => updateBookingStatus(booking.id, 'aprovado')}
                    className="btn-success flex items-center gap-2"
                    title="Aprovar agendamento"
                  >
                    <Check className="w-4 h-4" />
                    Aprovar
                  </button>
                  <button
                    onClick={() => updateBookingStatus(booking.id, 'rejeitado')}
                    className="btn-danger flex items-center gap-2"
                    title="Rejeitar agendamento"
                  >
                    <X className="w-4 h-4" />
                    Rejeitar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default PendingBookings