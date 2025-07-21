import styles from "./page.module.css";
import { motion } from "framer-motion";

/**
 * 首頁元件，顯示出缺席系統簡介與主要功能
 */
export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <motion.h1 initial={{ opacity: 0, y: -30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
          Attendance System
        </motion.h1>
        <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9 }}>
          A modern, secure, and user-friendly platform for managing class attendance.<br />
          Track, analyze, and manage attendance records with ease.
        </motion.p>
        <motion.ul initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.7 }} className={styles.features}>
          <li>✔️ Online attendance forms</li>
          <li>✔️ Real-time analytics</li>
          <li>✔️ Role-based access (Student/Teacher/Admin)</li>
          <li>✔️ Email notifications</li>
          <li>✔️ Location verification</li>
        </motion.ul>
        <motion.div className={styles.ctas} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8, duration: 0.7 }}>
          <a className={styles.primary} href="#">Get Started</a>
          <a className={styles.secondary} href="#">Learn More</a>
        </motion.div>
      </main>
      <Footer />
    </div>
  );
}

/**
 * 頁腳元件，包含 GitHub 與聯絡信箱
 */
function Footer() {
  return (
    <footer className={styles.footer}>
      <a href="https://github.com/yakiniku35/attendance_system" target="_blank" rel="noopener noreferrer">
        GitHub
      </a>
      <a href="mailto:support@example.com">Contact Support</a>
    </footer>
  );
}
