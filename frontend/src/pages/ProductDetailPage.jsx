import { useState } from 'react'

export default function ProductDetailPage({ product, onBack }) {
    const [selectedSize, setSelectedSize] = useState(null)

    const sizes = product.category === 'Footwear'
        ? ['UK 7', 'UK 8', 'UK 9', 'UK 10', 'UK 11']
        : ['S', 'M', 'L', 'XL']

    return (
        <main style={{ padding: '2rem 2.5rem', maxWidth: '1200px', margin: '0 auto' }}>
            <button
                onClick={onBack}
                style={{
                    background: 'none',
                    color: 'var(--muted)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '2rem',
                    fontSize: '0.9rem'
                }}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="m15 18-6-6 6-6" />
                </svg>
                Back to Shop
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(400px, 1.2fr) 1fr', gap: '4rem' }}>
                {/* Gallery */}
                <div style={{
                    background: 'var(--dark)',
                    borderRadius: 'var(--radius-xl)',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '600px',
                    border: '1px solid var(--dark-3)'
                }}>
                    <img
                        src={product.image_url}
                        alt={product.name}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                </div>

                {/* Details */}
                <div>
                    <span style={{
                        color: 'var(--accent)',
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        textTransform: 'uppercase',
                        letterSpacing: '1px'
                    }}>
                        {product.category}
                    </span>
                    <h1 style={{
                        fontFamily: 'var(--font-display)',
                        fontSize: '3.5rem',
                        marginTop: '0.5rem',
                        lineHeight: '1',
                        marginBottom: '1rem'
                    }}>
                        {product.name}
                    </h1>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                        <span style={{ fontSize: '2rem', fontWeight: '700' }}>₹{product.price.toLocaleString()}</span>
                        <span style={{
                            background: 'var(--dark-2)',
                            color: 'var(--muted)',
                            padding: '0.2rem 0.6rem',
                            borderRadius: 'var(--radius)',
                            fontSize: '0.8rem'
                        }}>
                            ★ {product.rating} (124 reviews)
                        </span>
                    </div>

                    <p style={{ color: 'var(--muted)', lineHeight: '1.7', marginBottom: '2.5rem', fontSize: '1rem' }}>
                        {product.description}
                    </p>

                    <div style={{ marginBottom: '2.5rem' }}>
                        <h4 style={{ fontSize: '0.9rem', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                            Select Size
                        </h4>
                        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                            {sizes.map(size => (
                                <button
                                    key={size}
                                    onClick={() => setSelectedSize(size)}
                                    style={{
                                        width: '64px',
                                        height: '48px',
                                        borderRadius: 'var(--radius)',
                                        background: selectedSize === size ? 'var(--white)' : 'var(--dark-2)',
                                        color: selectedSize === size ? 'var(--black)' : 'var(--white)',
                                        border: '1px solid ' + (selectedSize === size ? 'var(--white)' : 'var(--dark-4)'),
                                        fontWeight: '600',
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    {size}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button style={{
                            flex: 1,
                            background: 'var(--accent)',
                            color: 'var(--black)',
                            padding: '1.25rem',
                            borderRadius: 'var(--radius-lg)',
                            fontWeight: '700',
                            fontSize: '1rem',
                            textTransform: 'uppercase'
                        }}>
                            Add to Cart
                        </button>
                        <button style={{
                            width: '60px',
                            background: 'var(--dark-2)',
                            color: 'var(--white)',
                            borderRadius: 'var(--radius-lg)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid var(--dark-4)'
                        }}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                            </svg>
                        </button>
                    </div>

                    <div style={{ marginTop: '3rem', borderTop: '1px solid var(--dark-3)', paddingTop: '2rem' }}>
                        <div style={{ display: 'flex', gap: '2rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2">
                                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                                </svg>
                                <div style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                                    <div style={{ fontWeight: '600' }}>Fast Shipping</div>
                                    <div style={{ color: 'var(--muted)' }}>Delivery within 2-4 days</div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2">
                                    <path d="m21 8-2 2-2-2m0 10V6m0-4h.01M5 2h14c1.1 0 2 .9 2 2v16c0 1.1-.9 2-2 2H5c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2z" />
                                </svg>
                                <div style={{ fontSize: '0.75rem', lineHeight: '1.4' }}>
                                    <div style={{ fontWeight: '600' }}>Free Returns</div>
                                    <div style={{ color: 'var(--muted)' }}>30-day return policy</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    )
}
