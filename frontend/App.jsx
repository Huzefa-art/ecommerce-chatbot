import { useState } from 'react'
import HomePage from './pages/HomePage'
import ProductDetailPage from './pages/ProductDetailPage'
import ChatWidget from './components/ChatWidget'
import Navbar from './components/Navbar'

export default function App() {
  const [page, setPage] = useState('home')
  const [selectedProduct, setSelectedProduct] = useState(null)

  const navigate = (to, data = null) => {
    setPage(to)
    if (data) setSelectedProduct(data)
    window.scrollTo(0, 0)
  }

  return (
    <div className="app">
      <Navbar onNavigate={navigate} currentPage={page} />

      {page === 'home' && (
        <HomePage onSelectProduct={(p) => navigate('product', p)} />
      )}
      {page === 'product' && selectedProduct && (
        <ProductDetailPage
          product={selectedProduct}
          onBack={() => navigate('home')}
        />
      )}

      {/* Floating chat widget - always visible */}
      <ChatWidget />
    </div>
  )
}
