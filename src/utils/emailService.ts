// Email service utility
// This would integrate with your actual email service (SendGrid, AWS SES, etc.)

interface EmailData {
  to: string
  subject: string
  body: string
}

export const sendEmail = async (emailData: EmailData): Promise<boolean> => {
  try {
    // This is a placeholder for actual email service integration
    // In a real application, you would integrate with services like:
    // - SendGrid
    // - AWS SES
    // - Nodemailer with SMTP
    // - Supabase Edge Functions for server-side email sending
    
    console.log('Email would be sent:', emailData)
    
    // For now, we'll simulate a successful email send
    return true
  } catch (error) {
    console.error('Error sending email:', error)
    return false
  }
}

export const sendBookingNotification = async (
  userEmail: string,
  labName: string,
  date: string,
  status: 'aprovado' | 'rejeitado',
  description: string
): Promise<boolean> => {
  const subject = `Agendamento ${status.charAt(0).toUpperCase() + status.slice(1)}`
  const body = `
Olá,

Informamos que o seu agendamento para o espaço ${labName}, marcado para o dia ${date}, foi ${status}.

Descrição da atividade: ${description}

Caso necessite de esclarecimentos adicionais ou tenha dúvidas, por favor, entre em contato conosco.

Atenciosamente,
Equipe 🦉AgendaMCPF
  `.trim()

  return sendEmail({
    to: userEmail,
    subject,
    body
  })
}

export const sendBookingConfirmation = async (
  userEmail: string,
  labName: string,
  date: string,
  description: string
): Promise<boolean> => {
  const subject = "Confirmação de Solicitação de Agendamento"
  const body = `
Olá,

Seu agendamento para o espaço ${labName} marcado para o dia ${date} foi solicitado com sucesso e está pendente de aprovação.

Descrição da atividade: ${description}

Caso necessite de esclarecimentos adicionais ou tenha dúvidas, por favor, entre em contato conosco.

Atenciosamente,
Equipe 🦉AgendaMCPF
  `.trim()

  return sendEmail({
    to: userEmail,
    subject,
    body
  })
}