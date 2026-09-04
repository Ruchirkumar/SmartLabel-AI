import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Mail,
} from "lucide-react";
import { Link } from "react-router-dom";

import AuthShell from "../../components/auth/AuthShell";
import api from "../../services/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [resetLink, setResetLink] = useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    setError("");
    setResetLink("");
    setIsLoading(true);

    try {
      const response = await api.post(
        "/auth/forgot-password",
        {
          email: email.trim().toLowerCase(),
        },
      );

      setSent(true);

      // Development-only reset link.
      // Production will send this through email.
      if (response.data?.reset_link) {
        setResetLink(response.data.reset_link);
      }
    } catch (error: any) {
      console.error(
        "Forgot password error:",
        error,
      );

      const message =
        error?.response?.data?.detail ||
        "Unable to process your request. Please try again.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthShell>
      <motion.div
        className="login-container"
        initial={{
          opacity: 0,
          y: 20,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
        transition={{
          duration: 0.65,
        }}
      >
        {!sent ? (
          <>
            <div className="login-heading">
              <div className="welcome-label">
                <span className="welcome-line" />
                ACCOUNT RECOVERY
              </div>

              <h2>
                Forgot your
                <span> password?</span>
              </h2>

              <p>
                Enter your email address and we'll
                help you securely reset your password.
              </p>
            </div>

            {error && (
              <motion.div
                initial={{
                  opacity: 0,
                  y: -5,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                style={{
                  marginBottom: "18px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border:
                    "1px solid rgba(255, 90, 90, 0.25)",
                  background:
                    "rgba(255, 90, 90, 0.08)",
                  color: "#ff8f8f",
                  fontSize: "13px",
                  lineHeight: 1.5,
                }}
              >
                {error}
              </motion.div>
            )}

            <form
              onSubmit={handleSubmit}
              className="login-form"
            >
              <div className="field">
                <label htmlFor="forgot-email">
                  Email address
                </label>

                <div className="input-wrapper">
                  <Mail
                    size={18}
                    className="input-icon"
                  />

                  <input
                    id="forgot-email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(event) =>
                      setEmail(event.target.value)
                    }
                    autoComplete="email"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <motion.button
                type="submit"
                className="login-button"
                whileHover={
                  !isLoading ? { y: -2 } : {}
                }
                whileTap={
                  !isLoading
                    ? { scale: 0.985 }
                    : {}
                }
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <span
                      style={{
                        width: "16px",
                        height: "16px",
                        border:
                          "2px solid rgba(0,0,0,0.25)",
                        borderTopColor:
                          "#06130d",
                        borderRadius: "50%",
                        display: "inline-block",
                        animation:
                          "spin 0.7s linear infinite",
                      }}
                    />

                    <span>
                      Sending...
                    </span>
                  </>
                ) : (
                  <>
                    <span>
                      Send reset link
                    </span>

                    <ArrowRight size={18} />
                  </>
                )}
              </motion.button>
            </form>

            <p className="signup-text">
              <Link to="/login">
                <ArrowLeft size={14} />
                Back to sign in
              </Link>
            </p>
          </>
        ) : (
          <motion.div
            initial={{
              opacity: 0,
              scale: 0.96,
            }}
            animate={{
              opacity: 1,
              scale: 1,
            }}
            transition={{
              duration: 0.5,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                marginBottom: "22px",
              }}
            >
              <div
                style={{
                  width: "64px",
                  height: "64px",
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background:
                    "rgba(85, 255, 170, 0.10)",
                  border:
                    "1px solid rgba(85, 255, 170, 0.20)",
                }}
              >
                <CheckCircle2
                  size={32}
                />
              </div>
            </div>

            <div className="login-heading">
              <div className="welcome-label">
                <span className="welcome-line" />
                REQUEST RECEIVED
              </div>

              <h2>
                Check your
                <span> inbox.</span>
              </h2>

              <p>
                If an account exists for{" "}
                <strong>{email}</strong>, a password
                reset link has been generated.
              </p>
            </div>

            {resetLink && (
              <motion.div
                initial={{
                  opacity: 0,
                  y: 10,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay: 0.2,
                }}
                style={{
                  marginTop: "20px",
                  padding: "14px",
                  borderRadius: "12px",
                  border:
                    "1px solid rgba(85, 255, 170, 0.18)",
                  background:
                    "rgba(85, 255, 170, 0.06)",
                }}
              >
                <div
                  style={{
                    fontSize: "11px",
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    opacity: 0.65,
                    marginBottom: "8px",
                  }}
                >
                  Development reset link
                </div>

                <a
                  href={resetLink}
                  style={{
                    fontSize: "12px",
                    lineHeight: 1.5,
                    wordBreak: "break-all",
                  }}
                >
                  {resetLink}
                </a>

                <div
                  style={{
                    marginTop: "8px",
                    fontSize: "11px",
                    opacity: 0.55,
                  }}
                >
                  This link expires in 15 minutes.
                </div>
              </motion.div>
            )}

            <p className="signup-text">
              <Link to="/login">
                <ArrowLeft size={14} />
                Back to sign in
              </Link>
            </p>
          </motion.div>
        )}
      </motion.div>
    </AuthShell>
  );
}