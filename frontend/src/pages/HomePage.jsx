import { DEMO_PRODUCTS, CATEGORIES } from '../demoData'
import { useState } from 'react'

export default function HomePage({ onSelectProduct }) {
    const [activeCategory, setActiveCategory] = useState('All')

    const filteredProducts = activeCategory === 'All'
        ? DEMO_PRODUCTS
        : DEMO_PRODUCTS.filter(p => p.category === activeCategory)

    return (
        <main style={{ padding: '2rem 2.5rem' }}>
            <header style={{ marginBottom: '3rem' }}>
                <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '4rem', marginBottom: '1rem' }}>
                    LEVEL UP YOUR <span style={{ color: 'var(--accent)' }}>GAME</span>
                </h1>
                <p style={{ color: 'var(--muted)', maxWidth: '600px', lineHeight: '1.6' }}>
                    Discover the latest in high-performance footwear and apparel.
                    Engineered for athletes, designed for the street.
                </p>
            </header>

            <div style={{ display: 'flex', gap: '1rem', marginBottom: '2.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                {CATEGORIES.map(cat => (
                    <button
                        key={cat}
                        onClick={() => setActiveCategory(cat)}
                        style={{
                            padding: '0.6rem 1.5rem',
                            borderRadius: 'var(--radius-xl)',
                            background: activeCategory === cat ? 'var(--accent)' : 'var(--dark-2)',
                            color: activeCategory === cat ? 'var(--black)' : 'var(--white)',
                            fontWeight: '600',
                            fontSize: '0.85rem',
                            whiteSpace: 'nowrap',
                            transition: 'all 0.2s ease'
                        }}
                    >
                        {cat}
                    </button>
                ))}
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '2rem'
            }}>
                {filteredProducts.map(product => (
                    <div
                        key={product.id}
                        onClick={() => onSelectProduct(product)}
                        style={{
                            background: 'var(--dark)',
                            borderRadius: 'var(--radius-lg)',
                            overflow: 'hidden',
                            cursor: 'pointer',
                            transition: 'transform 0.3s ease',
                            border: '1px solid var(--dark-3)'
                        }}
                        onMouseOver={e => e.currentTarget.style.transform = 'translateY(-8px)'}
                        onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                        <div style={{ height: '320px', overflow: 'hidden', background: '#222' }}>
                            <img
                                src={product.image_url}
                                alt={product.name}
                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            />
                        </div>
                        <div style={{ padding: '1.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: '600', textTransform: 'uppercase' }}>
                                    {product.category}
                                </span>
                                <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>★ {product.rating}</span>
                            </div>
                            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', fontWeight: '600' }}>{product.name}</h3>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '1.25rem', fontWeight: '700' }}>₹{product.price.toLocaleString()}</span>
                                <button style={{
                                    background: 'var(--white)',
                                    color: 'var(--black)',
                                    padding: '0.5rem 1rem',
                                    borderRadius: 'var(--radius)',
                                    fontSize: '0.8rem',
                                    fontWeight: '600'
                                }}>
                                    View Details
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </main>
    )
}
