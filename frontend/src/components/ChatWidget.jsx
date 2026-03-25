import { useState, useEffect, useRef } from 'react'
import { useChatApi } from '../useChatApi'
import styles from './ChatWidget.module.css'

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false)
    const [message, setMessage] = useState('')
    const [chatLog, setChatLog] = useState([
        { role: 'assistant', text: 'Hey there! ⚡ Welcome to APEX SPORT. How can I help you today? I can find products, check stock, or answer brand questions!' }
    ])

    const { sendMessage, isLoading } = useChatApi()
    const scrollRef = useRef(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [chatLog])

    const handleSend = async (e) => {
        e.preventDefault()
        if (!message.trim() || isLoading) return

        const userMsg = message.trim()
        setMessage('')
        setChatLog(prev => [...prev, { role: 'user', text: userMsg }])

        try {
            const response = await sendMessage(userMsg)
            setChatLog(prev => [...prev, {
                role: 'assistant',
                text: response.message,
                products: response.products
            }])
        } catch (err) {
            setChatLog(prev => [...prev, { role: 'assistant', text: "Sorry, I'm having trouble connecting right now. 🚧 Please try again later." }])
        }
    }

    return (
        <div className={styles.widget}>
            {/* Toggle Button */}
            <button
                className={`${styles.toggle} ${isOpen ? styles.active : ''}`}
                onClick={() => setIsOpen(!isOpen)}
                aria-label="Toggle Chat"
            >
                {isOpen ? (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M18 6 6 18M6 6l12 12" />
                    </svg>
                ) : (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                )}
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className={styles.window}>
                    <div className={styles.header}>
                        <div className={styles.headerInfo}>
                            <div className={styles.avatar}>AI</div>
                            <div>
                                <div className={styles.title}>Apex Assistant</div>
                                <div className={styles.status}>Online & Ready</div>
                            </div>
                        </div>
                    </div>

                    <div className={styles.messages} ref={scrollRef}>
                        {chatLog.map((chat, i) => (
                            <div key={i} className={`${styles.message} ${chat.role === 'user' ? styles.user : styles.assistant}`}>
                                <div className={styles.bubble}>
                                    {chat.text}

                                    {chat.products && chat.products.length > 0 && (
                                        <div className={styles.productScroll}>
                                            {chat.products.map(p => (
                                                <div key={p.id} className={styles.productCard}>
                                                    {p.image_url && <img src={p.image_url} alt={p.name} />}
                                                    <div className={styles.productInfo}>
                                                        <div className={styles.pName}>{p.name}</div>
                                                        <div className={styles.pPrice}>Rs. {p.price.toLocaleString()}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className={styles.message + ' ' + styles.assistant}>
                                <div className={styles.bubble}>
                                    <div className={styles.typing}>
                                        <span></span><span></span><span></span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <form className={styles.inputArea} onSubmit={handleSend}>
                        <input
                            type="text"
                            placeholder="Ask anything..."
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            disabled={isLoading}
                        />
                        <button type="submit" disabled={!message.trim() || isLoading}>
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
                            </svg>
                        </button>
                    </form>
                </div>
            )}
        </div>
    )
}
