import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
} from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import AuthShell from "../../components/auth/AuthShell";
import api from "../../services/api";

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (isLoading) {
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email: email.trim().toLowerCase(),
        password,
      });

      const accessToken = response.data?.access_token;
      const user = response.data?.user;

      if (!accessToken) {
        throw new Error(
          "Login succeeded but the server did not return an access token."
        );
      }

      if (!user) {
        throw new Error(
          "Login succeeded but the server did not return user information."
        );
      }

      localStorage.setItem(
        "smartlabel_token",
        accessToken
      );

      localStorage.setItem(
        "smartlabel_user",
        JSON.stringify(user)
      );

      if (rememberMe) {
        localStorage.setItem(
          "smartlabel_remember",
          "true"
        );
      } else {
        localStorage.removeItem(
          "smartlabel_remember"
        );
      }

      try {
        const meResponse = await api.get("/auth/me");

        const verifiedUser = meResponse.data?.user;

        if (verifiedUser) {
          localStorage.setItem(
            "smartlabel_user",
            JSON.stringify(verifiedUser)
          );
        }
      } catch (verificationError: any) {
        console.error(
          "Token verification failed:",
          verificationError
        );

        localStorage.removeItem(
          "smartlabel_token"
        );

        localStorage.removeItem(
          "smartlabel_user"
        );

        throw new Error(
          verificationError?.response?.data?.detail ||
            "Login succeeded, but the authentication token could not be verified."
        );
      }

      const savedToken =
        localStorage.getItem("smartlabel_token");

      if (!savedToken) {
        throw new Error(
          "Authentication token was not saved. Please try again."
        );
      }

      navigate("/dashboard", {
        replace: true,
      });
    } catch (error: any) {
      console.error("Login error:", error);

      let message =
        "Unable to sign in. Please try again.";

      if (error?.response?.data?.detail) {
        message = error.response.data.detail;
      } else if (error?.message) {
        message = error.message;
      }

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  function handleGoogleLogin() {
    if (isLoading) {
      return;
    }

    setError("");

    /*
     * Google OAuth is handled by the FastAPI backend.
     *
     * Flow:
     * Login page
     *    ↓
     * FastAPI /auth/google/login
     *    ↓
     * Google
     *    ↓
     * FastAPI /auth/google/callback
     *    ↓
     * Frontend Google callback handler
     *    ↓
     * Dashboard
     */

    window.location.href =
      "http://localhost:8000/api/auth/google/login";
  }

  /*
   * If Google OAuth redirects back to /login?google_error=1,
   * show a useful error instead of silently failing.
   */
  const googleError = searchParams.get("google_error");

  const displayError =
    error ||
    (googleError
      ? "Google sign-in failed. Please try again."
      : "");

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
            WELCOME BACK
          </div>

          <h2>
            Sign in to
            <span> SmartLabel.</span>
          </h2>

          <p>
            Continue checking packaged commodity
            labels with SmartLabel AI.
          </p>
        </div>

        {displayError && (
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
            {displayError}
          </motion.div>
        )}

        <form
          onSubmit={handleSubmit}
          className="login-form"
        >
          <div className="field">
            <label htmlFor="login-email">
              Email address
            </label>

            <div className="input-wrapper">
              <Mail
                size={18}
                className="input-icon"
              />

              <input
                id="login-email"
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

          <div className="field">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <label htmlFor="login-password">
                Password
              </label>

              <Link
                to="/forgot-password"
                style={{
                  fontSize: "12px",
                }}
              >
                Forgot password?
              </Link>
            </div>

            <div className="input-wrapper">
              <LockKeyhole
                size={18}
                className="input-icon"
              />

              <input
                id="login-password"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                autoComplete="current-password"
                required
                disabled={isLoading}
              />

              <button
                type="button"
                className="input-action"
                onClick={() =>
                  setShowPassword(
                    (current) => !current
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

          <label className="remember-row">
            <span
              className={`custom-checkbox ${
                rememberMe ? "checked" : ""
              }`}
            >
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(event) =>
                  setRememberMe(
                    event.target.checked
                  )
                }
                disabled={isLoading}
              />

              {rememberMe && (
                <span
                  style={{
                    fontSize: "11px",
                  }}
                >
                  ✓
                </span>
              )}
            </span>

            <span className="remember-text">
              Remember me
            </span>
          </label>

          <motion.button
            type="submit"
            className="login-button"
            whileHover={
              !isLoading
                ? { y: -2 }
                : {}
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
                  Signing in...
                </span>
              </>
            ) : (
              <>
                <span>
                  Sign in
                </span>

                <ArrowRight size={18} />
              </>
            )}
          </motion.button>
        </form>

        <div className="divider">
          <span />
          <strong>OR</strong>
          <span />
        </div>

        <button
          type="button"
          className="google-button"
          onClick={handleGoogleLogin}
          disabled={isLoading}
        >
          <span className="google-logo">
            G
          </span>

          <span>
            Continue with Google
          </span>
        </button>

        <p className="signup-text">
          <span>
            Don't have an account?
          </span>

          <Link to="/register">
            Create account
            <ArrowRight size={14} />
          </Link>
        </p>
      </motion.div>
    </AuthShell>
  );
}