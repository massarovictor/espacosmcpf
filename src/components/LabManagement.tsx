import React, { useState, useEffect } from 'react'
import { useSupabase } from '../contexts/SupabaseContext'
import { Building2, Plus, Edit, Trash2, Users, User } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'
import Modal from './Modal'
import ConfirmDialog from './ConfirmDialog'
import toast from 'react-hot-toast'

interface Lab {
  id: string
  nome: string
  descricao: string
  capacidade: number
  administrador_id: string | null
  admin_name?: string
  admin_email?: string
}

interface Admin {
  id: string
  name: string
  email: string
}

interface LabFormData {
  nome: string
  descricao: string
  capacidade: number
  administrador_id: string
}

const LabManagement: React.FC = () => {
  const [labs, setLabs] = useState<Lab[]>([])
  const [admins, setAdmins] = useState<Admin[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [selectedLab, setSelectedLab] = useState<Lab | null>(null)
  const [formData, setFormData] = useState<LabFormData>({
    nome: '',
    descricao: '',
    capacidade: 0,
    administrador_id: ''
  })
  const { supabase } = useSupabase()

  useEffect(() => {
    fetchLabs()
    fetchAdmins()
  }, [])

  const fetchLabs = async () => {
    try {
      const { data, error } = await supabase
        .from('laboratorios')
        .select('*')
        .order('nome')

      if (error) throw error

      // Enrich labs with admin info
      const enrichedLabs = await Promise.all(
        (data || []).map(async (lab) => {
          if (lab.administrador_id) {
            const { data: adminData } = await supabase
              .from('users')
              .select('name, email')
              .eq('id', lab.administrador_id)
              .single()

            return {
              ...lab,
              admin_name: adminData?.name,
              admin_email: adminData?.email
            }
          }
          return lab
        })
      )

      setLabs(enrichedLabs)
    } catch (error) {
      console.error('Error fetching labs:', error)
      toast.error('Erro ao carregar laboratórios')
    } finally {
      setLoading(false)
    }
  }

  const fetchAdmins = async () => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('id, name, email')
        .eq('tipo_usuario', 'admlab')
        .order('name')

      if (error) throw error
      setAdmins(data || [])
    } catch (error) {
      console.error('Error fetching admins:', error)
    }
  }

  const handleAddLab = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.nome.trim()) {
      toast.error('O nome do laboratório é obrigatório')
      return
    }

    // Check for duplicate names
    const normalizedName = formData.nome.trim().toLowerCase().replace(/\s+/g, ' ')
    const existingLab = labs.find(lab => 
      lab.nome.trim().toLowerCase().replace(/\s+/g, ' ') === normalizedName
    )

    if (existingLab) {
      toast.error('Já existe um laboratório com este nome')
      return
    }

    try {
      const { error } = await supabase
        .from('laboratorios')
        .insert({
          nome: formData.nome.trim(),
          descricao: formData.descricao.trim(),
          capacidade: formData.capacidade,
          administrador_id: formData.administrador_id || null
        })

      if (error) throw error

      toast.success('Laboratório adicionado com sucesso!')
      setShowAddModal(false)
      resetForm()
      fetchLabs()
    } catch (error) {
      console.error('Error adding lab:', error)
      toast.error('Erro ao adicionar laboratório')
    }
  }

  const handleEditLab = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedLab) return

    if (!formData.nome.trim()) {
      toast.error('O nome do laboratório é obrigatório')
      return
    }

    try {
      const { error } = await supabase
        .from('laboratorios')
        .update({
          nome: formData.nome.trim(),
          descricao: formData.descricao.trim(),
          capacidade: formData.capacidade,
          administrador_id: formData.administrador_id || null
        })
        .eq('id', selectedLab.id)

      if (error) throw error

      toast.success('Laboratório atualizado com sucesso!')
      setShowEditModal(false)
      resetForm()
      fetchLabs()
    } catch (error) {
      console.error('Error updating lab:', error)
      toast.error('Erro ao atualizar laboratório')
    }
  }

  const handleDeleteLab = async () => {
    if (!selectedLab) return

    try {
      const { error } = await supabase
        .from('laboratorios')
        .delete()
        .eq('id', selectedLab.id)

      if (error) throw error

      toast.success('Laboratório excluído com sucesso!')
      setShowDeleteDialog(false)
      setSelectedLab(null)
      fetchLabs()
    } catch (error) {
      console.error('Error deleting lab:', error)
      toast.error('Erro ao excluir laboratório')
    }
  }

  const resetForm = () => {
    setFormData({
      nome: '',
      descricao: '',
      capacidade: 0,
      administrador_id: ''
    })
    setSelectedLab(null)
  }

  const openEditModal = (lab: Lab) => {
    setSelectedLab(lab)
    setFormData({
      nome: lab.nome,
      descricao: lab.descricao || '',
      capacidade: lab.capacidade || 0,
      administrador_id: lab.administrador_id || ''
    })
    setShowEditModal(true)
  }

  const openDeleteDialog = (lab: Lab) => {
    setSelectedLab(lab)
    setShowDeleteDialog(true)
  }

  if (loading) {
    return <LoadingSpinner className="py-8" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gerenciar Espaços</h2>
          <p className="text-gray-600">Adicione e gerencie os espaços do sistema</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Adicionar Espaço
        </button>
      </div>

      {/* Labs List */}
      {labs.length === 0 ? (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Nenhum espaço cadastrado</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {labs.map((lab) => (
            <div key={lab.id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{lab.nome}</h3>
                    {lab.capacidade > 0 && (
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Users className="w-3 h-3" />
                        {lab.capacidade} pessoas
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => openEditModal(lab)}
                    className="text-primary-600 hover:text-primary-900 p-1 rounded-md hover:bg-primary-50"
                    title="Editar laboratório"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openDeleteDialog(lab)}
                    className="text-red-600 hover:text-red-900 p-1 rounded-md hover:bg-red-50"
                    title="Excluir laboratório"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {lab.descricao && (
                <p className="text-gray-600 text-sm mb-4">{lab.descricao}</p>
              )}

              <div className="border-t pt-4">
                <div className="flex items-center gap-2 text-sm">
                  <User className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Administrador:</span>
                  <span className="text-gray-900">
                    {lab.admin_name || lab.admin_email || 'Não atribuído'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Lab Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false)
          resetForm()
        }}
        title="Adicionar Novo Espaço"
      >
        <form onSubmit={handleAddLab} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome do Espaço *
              </label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                className="input-field"
                placeholder="Digite o nome do espaço"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Capacidade
              </label>
              <input
                type="number"
                value={formData.capacidade}
                onChange={(e) => setFormData({ ...formData, capacidade: parseInt(e.target.value) || 0 })}
                className="input-field"
                placeholder="Capacidade máxima"
                min="0"
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
              placeholder="Descrição opcional do espaço"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Administrador do Espaço
            </label>
            <select
              value={formData.administrador_id}
              onChange={(e) => setFormData({ ...formData, administrador_id: e.target.value })}
              className="input-field"
            >
              <option value="">Não atribuído</option>
              {admins.map((admin) => (
                <option key={admin.id} value={admin.id}>
                  {admin.name || admin.email}
                </option>
              ))}
            </select>
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
              Adicionar Espaço
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Lab Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false)
          resetForm()
        }}
        title={`Editar Espaço: ${selectedLab?.nome}`}
      >
        <form onSubmit={handleEditLab} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome do Espaço *
              </label>
              <input
                type="text"
                value={formData.nome}
                onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                className="input-field"
                placeholder="Digite o nome do espaço"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Capacidade
              </label>
              <input
                type="number"
                value={formData.capacidade}
                onChange={(e) => setFormData({ ...formData, capacidade: parseInt(e.target.value) || 0 })}
                className="input-field"
                placeholder="Capacidade máxima"
                min="0"
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
              placeholder="Descrição opcional do espaço"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Administrador do Espaço
            </label>
            <select
              value={formData.administrador_id}
              onChange={(e) => setFormData({ ...formData, administrador_id: e.target.value })}
              className="input-field"
            >
              <option value="">Não atribuído</option>
              {admins.map((admin) => (
                <option key={admin.id} value={admin.id}>
                  {admin.name || admin.email}
                </option>
              ))}
            </select>
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
              Atualizar Dados
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => {
          setShowDeleteDialog(false)
          setSelectedLab(null)
        }}
        onConfirm={handleDeleteLab}
        title="Excluir Espaço"
        message={`Tem certeza que deseja excluir o espaço "${selectedLab?.nome}"? Esta ação não pode ser desfeita.`}
        confirmText="Excluir"
        confirmButtonClass="btn-danger"
      />
    </div>
  )
}

export default LabManagement