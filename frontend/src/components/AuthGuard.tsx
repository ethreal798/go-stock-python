import React, { useEffect, useState } from 'react'
import { Modal, Button } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface AuthGuardProps {
  children: React.ReactNode
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, isGuestMode, setGuestMode } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    // 如果未登录且不是游客模式，显示弹窗
    if (!isAuthenticated && !isGuestMode) {
      setShowModal(true)
    } else {
      setShowModal(false)
    }
  }, [isAuthenticated, isGuestMode, location.pathname])

  const handleGoLogin = () => {
    setShowModal(false)
    navigate('/login')
  }

  const handleGuestMode = () => {
    setShowModal(false)
    setGuestMode(true)
  }

  // 渲染子组件，但如果是游客模式，逻辑将由子组件内部根据 isGuestMode 禁用功能
  return (
    <>
      {children}
      <Modal
        title="登录提示"
        open={showModal}
        closable={false}
        maskClosable={false}
        footer={[
          <Button key="guest" onClick={handleGuestMode}>
            暂不登录
          </Button>,
          <Button key="login" type="primary" onClick={handleGoLogin}>
            去登录
          </Button>,
        ]}
      >
        <p>该功能需要登录才能使用，您可以选择暂不登录以浏览内容（部分功能受限），或前往登录以解锁全部功能。</p>
      </Modal>
    </>
  )
}

export default AuthGuard
