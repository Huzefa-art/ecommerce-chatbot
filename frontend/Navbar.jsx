import styles from './Navbar.module.css'

export default function Navbar({ onNavigate, currentPage }) {
  return (
    <nav className={styles.nav}>
      <button className={styles.logo} onClick={() => onNavigate('home')}>
        <span className={styles.logoIcon}>⚡</span>
        <span className={styles.logoText}>APEX</span>
        <span className={styles.logoSub}>SPORT</span>
      </button>

      <div className={styles.links}>
        <button
          className={`${styles.link} ${currentPage === 'home' ? styles.active : ''}`}
          onClick={() => onNavigate('home')}
        >
          Shop
        </button>
        <button className={styles.link}>Collections</button>
        <button className={styles.link}>About</button>
      </div>

      <div className={styles.actions}>
        <button className={styles.iconBtn} aria-label="Search">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </button>
        <button className={styles.iconBtn} aria-label="Cart">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <path d="M16 10a4 4 0 0 1-8 0"/>
          </svg>
        </button>
      </div>
    </nav>
  )
}
