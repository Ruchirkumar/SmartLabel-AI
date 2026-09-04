import { motion } from "motion/react";
import {
  ScanLine,
  ShieldCheck,
  Sparkles,
  Sun,
  Moon,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import Galaxy from "../common/Galaxy";

interface AuthShellProps {
  children: ReactNode;
}

export default function AuthShell({
  children,
}: AuthShellProps) {
  const [darkMode, setDarkMode] = useState(true);

  useEffect(() => {
    const savedTheme =
      localStorage.getItem("smartlabel-theme");

    const isDark =
      savedTheme
        ? savedTheme === "dark"
        : true;

    setDarkMode(isDark);

    document.documentElement.classList.toggle(
      "dark",
      isDark
    );
  }, []);

  const toggleTheme = () => {
    const nextTheme = !darkMode;

    setDarkMode(nextTheme);

    document.documentElement.classList.toggle(
      "dark",
      nextTheme
    );

    localStorage.setItem(
      "smartlabel-theme",
      nextTheme ? "dark" : "light"
    );
  };

  return (
    <main className="auth-page">

      {/* =========================================
          GALAXY BACKGROUND
      ========================================= */}

      <div className="galaxy-background">
        <Galaxy
          mouseRepulsion
          mouseInteraction
          density={1.15}
          glowIntensity={0.42}
          saturation={0.28}
          hueShift={145}
          twinkleIntensity={0.4}
          rotationSpeed={0.035}
          repulsionStrength={2.2}
          autoCenterRepulsion={0}
          starSpeed={0.35}
          speed={0.7}
          transparent
        />
      </div>

      {/* =========================================
          ATMOSPHERIC OVERLAY
      ========================================= */}

      <div className="galaxy-overlay" />

      <div className="auth-noise" />

      {/* =========================================
          LEFT SHOWCASE
      ========================================= */}

      <section className="auth-showcase">

        {/* BRAND */}

        <motion.div
          className="brand"
          initial={{
            opacity: 0,
            y: -15,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.6,
          }}
        >
          <div className="brand-icon">
            <ScanLine size={24} />
          </div>

          <div className="brand-text">
            <div className="brand-name">
              SmartLabel
            </div>

            <div className="brand-ai">
              AI
            </div>
          </div>
        </motion.div>

        {/* HERO CONTENT */}

        <motion.div
          className="showcase-content"
          initial={{
            opacity: 0,
            x: -30,
          }}
          animate={{
            opacity: 1,
            x: 0,
          }}
          transition={{
            duration: 0.8,
            delay: 0.15,
          }}
        >

          <div className="eyebrow">
            <Sparkles size={15} />

            <span>
              AI-POWERED COMPLIANCE
            </span>
          </div>

          <h1>
            Make every
            <span>
              {" "}label compliant.
            </span>
          </h1>

          <p>
            Scan packaged commodity labels,
            extract mandatory declarations,
            and identify potential Legal
            Metrology compliance issues in
            seconds.
          </p>

        </motion.div>

        {/* =========================================
            LIVE ANALYSIS CARD
        ========================================= */}

        <motion.div
          className="scan-card"
          initial={{
            opacity: 0,
            y: 30,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.8,
            delay: 0.35,
          }}
        >

          {/* HEADER */}

          <div className="scan-card-header">

            <div className="scan-status">

              <span className="status-dot" />

              <span>
                LIVE ANALYSIS
              </span>

            </div>

            <span className="engine-name">
              SmartLabel Engine
            </span>

          </div>

          {/* SCAN AREA */}

          <div className="scan-visual">

            <div className="scan-corner scan-corner-tl" />
            <div className="scan-corner scan-corner-tr" />
            <div className="scan-corner scan-corner-bl" />
            <div className="scan-corner scan-corner-br" />

            <motion.div
              className="package-outline"
              animate={{
                y: [0, -3, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >

              <div className="package-top">
                PREMIUM
              </div>

              <div className="package-main">
                FOOD
              </div>

              <div className="package-quantity">
                NET QTY 500 g
              </div>

              <div className="package-mrp">
                MRP ₹120.00
              </div>

            </motion.div>

            {/* SCANNING LINE */}

            <motion.div
              className="scan-line"
              animate={{
                top: [
                  "8%",
                  "88%",
                  "8%",
                ],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

          </div>

          {/* ANALYSIS TAGS */}

          <div className="analysis-tags">

            <span>
              <ShieldCheck size={14} />
              MRP
            </span>

            <span>
              <ShieldCheck size={14} />
              Quantity
            </span>

            <span>
              <ShieldCheck size={14} />
              Manufacturer
            </span>

          </div>

        </motion.div>

      </section>

      {/* =========================================
          RIGHT AUTH PANEL
      ========================================= */}

      <section className="auth-panel">

        {/* THEME BUTTON */}

        <motion.button
          type="button"
          className="theme-toggle"
          aria-label="Toggle theme"
          onClick={toggleTheme}
          whileHover={{
            scale: 1.05,
          }}
          whileTap={{
            scale: 0.95,
          }}
        >
          {darkMode ? (
            <Sun size={18} />
          ) : (
            <Moon size={18} />
          )}
        </motion.button>

        {/* GLASS CONTENT */}

        <motion.div
          className="auth-panel-inner"
          initial={{
            opacity: 0,
            x: 25,
          }}
          animate={{
            opacity: 1,
            x: 0,
          }}
          transition={{
            duration: 0.7,
            delay: 0.15,
          }}
        >
          {children}
        </motion.div>

        {/* BOTTOM BRANDING */}

        <div className="auth-footer">
          <span>
            SmartLabel AI
          </span>

          <span className="footer-dot">
            •
          </span>

          <span>
            Legal Metrology Intelligence
          </span>
        </div>

      </section>

    </main>
  );
}