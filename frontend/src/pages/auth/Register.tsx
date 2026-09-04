import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  User,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import AuthShell from "../../components/auth/AuthShell";
import api from "../../services/api";

export default function Register() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] =
    useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] =
    useState("");

  const [accepted, setAccepted] =
    useState(false);

  const [isLoading, setIsLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    // Prevent accidental double submission
    if (isLoading) {
      return;
    }

    setError("");

    const cleanName = name.trim();
    const cleanEmail =
      email.trim().toLowerCase();

    // Validate name
    if (cleanName.length < 2) {
      setError(
        "Name must be at least 2 characters."
      );
      return;
    }

    // Validate email
    if (!cleanEmail) {
      setError(
        "Please enter your email address."
      );
      return;
    }

    // Validate password
    if (password.length < 8) {
      setError(
        "Password must be at least 8 characters."
      );
      return;
    }

    // Validate terms
    if (!accepted) {
      setError(
        "Please accept the terms and privacy policy."
      );
      return;
    }

    try {
      setIsLoading(true);

      // ==================================================
      // STEP 1 — REGISTER
      // ==================================================

      const response = await api.post(
        "/auth/register",
        {
          name: cleanName,
          email: cleanEmail,
          password,
        }
      );

      const accessToken =
        response.data?.access_token;

      const user =
        response.data?.user;

      // Make sure backend returned authentication data
      if (!accessToken) {
        throw new Error(
          "Account was created, but the server did not return an access token."
        );
      }

      if (!user) {
        throw new Error(
          "Account was created, but the server did not return user information."
        );
      }

      // ==================================================
      // STEP 2 — STORE AUTHENTICATION DATA
      // ==================================================

      localStorage.setItem(
        "smartlabel_token",
        accessToken
      );

      localStorage.setItem(
        "smartlabel_user",
        JSON.stringify(user)
      );

      // ==================================================
      // STEP 3 — VERIFY TOKEN
      //
      // Make registration authentication behave
      // consistently with the Login flow.
      // ==================================================

      try {
        const meResponse =
          await api.get("/auth/me");

        const verifiedUser =
          meResponse.data?.user;

        if (verifiedUser) {
          localStorage.setItem(
            "smartlabel_user",
            JSON.stringify(verifiedUser)
          );
        }
      } catch (verificationError: any) {
        console.error(
          "Registration token verification failed:",
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
            "Account was created, but the authentication token could not be verified."
        );
      }

      // ==================================================
      // STEP 4 — FINAL TOKEN CHECK
      // ==================================================

      const savedToken =
        localStorage.getItem(
          "smartlabel_token"
        );

      if (!savedToken) {
        throw new Error(
          "Authentication token was not saved. Please try again."
        );
      }

      // ==================================================
      // STEP 5 — DASHBOARD
      // ==================================================

      navigate("/dashboard", {
        replace: true,
      });

    } catch (error: any) {
      console.error(
        "Registration error:",
        error
      );

      const message =
        error?.response?.data?.detail ||
        error?.message ||
        "Unable to create account. Please try again.";

      setError(message);

    } finally {
      setIsLoading(false);
    }
  }

  // ====================================================
  // GOOGLE SIGNUP
  // ====================================================

  function handleGoogleSignup() {
    setError(
      "Google sign-up is not connected yet. Please use email and password."
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
            GET STARTED
          </div>

          <h2>
            Create your
            <span> workspace.</span>
          </h2>

          <p>
            Start checking packaged commodity
            labels with SmartLabel AI.
          </p>
        </div>

        {/* Error message */}
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
            }}
          >
            {error}
          </motion.div>
        )}

        <form
          onSubmit={handleSubmit}
          className="login-form"
        >
          {/* Name */}
          <div className="field">
            <label htmlFor="name">
              Full name
            </label>

            <div className="input-wrapper">
              <User
                size={18}
                className="input-icon"
              />

              <input
                id="name"
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value
                  )
                }
                autoComplete="name"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Email */}
          <div className="field">
            <label htmlFor="register-email">
              Email address
            </label>

            <div className="input-wrapper">
              <Mail
                size={18}
                className="input-icon"
              />

              <input
                id="register-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) =>
                  setEmail(
                    event.target.value
                  )
                }
                autoComplete="email"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Password */}
          <div className="field">
            <label htmlFor="register-password">
              Password
            </label>

            <div className="input-wrapper">
              <LockKeyhole
                size={18}
                className="input-icon"
              />

              <input
                id="register-password"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                placeholder="Create a password"
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value
                  )
                }
                autoComplete="new-password"
                minLength={8}
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

          {/* Terms */}
          <label className="remember-row">
            <span
              className={`custom-checkbox ${
                accepted ? "checked" : ""
              }`}
            >
              <input
                type="checkbox"
                checked={accepted}
                onChange={(event) =>
                  setAccepted(
                    event.target.checked
                  )
                }
                required
                disabled={isLoading}
              />

              {accepted && (
                <Check size={11} />
              )}
            </span>

            <span className="remember-text">
              I agree to the terms and privacy
              policy.
            </span>
          </label>

          {/* Create account */}
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
                  Creating account...
                </span>
              </>
            ) : (
              <>
                <span>
                  Create account
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

        {/* Google */}
        <button
          type="button"
          className="google-button"
          onClick={handleGoogleSignup}
          disabled={isLoading}
        >
          <span className="google-logo">
            G
          </span>

          <span>
            Sign up with Google
          </span>
        </button>

        <p className="signup-text">
          <span>
            Already have an account?
          </span>

          <Link to="/login">
            Sign in
            <ArrowRight size={14} />
          </Link>
        </p>
      </motion.div>
    </AuthShell>
  );
}