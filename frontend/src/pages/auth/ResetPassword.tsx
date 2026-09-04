import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
} from "lucide-react";
import {
  Link,
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import AuthShell from "../../components/auth/AuthShell";
import api from "../../services/api";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const token = searchParams.get("token") || "";

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [showConfirmPassword, setShowConfirmPassword] =
    useState(false);

  const [isLoading, setIsLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState(false);

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    setError("");

    if (!token) {
      setError(
        "This password reset link is invalid.",
      );
      return;
    }

    if (password.length < 8) {
      setError(
        "Password must be at least 8 characters.",
      );
      return;
    }

    if (password !== confirmPassword) {
      setError(
        "Passwords do not match.",
      );
      return;
    }

    setIsLoading(true);

    try {
      await api.post(
        "/auth/reset-password",
        {
          token,
          new_password: password,
        },
      );

      setSuccess(true);
    } catch (error: any) {
      console.error(
        "Reset password error:",
        error,
      );

      const message =
        error?.response?.data?.detail ||
        "Unable to reset your password. Please request a new reset link.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  if (success) {
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
              PASSWORD UPDATED
            </div>

            <h2>
              You're all
              <span> set.</span>
            </h2>

            <p>
              Your SmartLabel password has been
              successfully updated.
            </p>
          </div>

          <motion.button
            type="button"
            className="login-button"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.985 }}
            onClick={() =>
              navigate("/login", {
                replace: true,
              })
            }
          >
            <span>
              Continue to sign in
            </span>

            <ArrowRight size={18} />
          </motion.button>
        </motion.div>
      </AuthShell>
    );
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
        <div className="login-heading">
          <div className="welcome-label">
            <span className="welcome-line" />
            SECURE RECOVERY
          </div>

          <h2>
            Create a new
            <span> password.</span>
          </h2>

          <p>
            Choose a strong password for your
            SmartLabel account.
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
            <label htmlFor="new-password">
              New password
            </label>

            <div className="input-wrapper">
              <LockKeyhole
                size={18}
                className="input-icon"
              />

              <input
                id="new-password"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                placeholder="At least 8 characters"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                required
                disabled={isLoading}
              />

              <button
                type="button"
                className="input-action"
                onClick={() =>
                  setShowPassword(
                    (current) => !current,
                  )
                }
                disabled={isLoading}
                aria-label={
                  showPassword
                    ? "Hide password"
                    : "Show password"
                }
              >
                {showPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>
            </div>
          </div>

          <div className="field">
            <label htmlFor="confirm-password">
              Confirm password
            </label>

            <div className="input-wrapper">
              <LockKeyhole
                size={18}
                className="input-icon"
              />

              <input
                id="confirm-password"
                type={
                  showConfirmPassword
                    ? "text"
                    : "password"
                }
                placeholder="Repeat your password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                required
                disabled={isLoading}
              />

              <button
                type="button"
                className="input-action"
                onClick={() =>
                  setShowConfirmPassword(
                    (current) => !current,
                  )
                }
                disabled={isLoading}
                aria-label={
                  showConfirmPassword
                    ? "Hide password"
                    : "Show password"
                }
              >
                {showConfirmPassword ? (
                  <EyeOff size={18} />
                ) : (
                  <Eye size={18} />
                )}
              </button>
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
                  Updating...
                </span>
              </>
            ) : (
              <>
                <span>
                  Update password
                </span>

                <ArrowRight size={18} />
              </>
            )}
          </motion.button>
        </form>

        <p className="signup-text">
          <Link to="/login">
            Back to sign in
            <ArrowRight size={14} />
          </Link>
        </p>
      </motion.div>
    </AuthShell>
  );
}