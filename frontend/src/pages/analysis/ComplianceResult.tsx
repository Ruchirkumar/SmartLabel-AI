import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  Info,
  ScanLine,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
  X,
} from "lucide-react";
import api from "../../services/api";

interface Analysis {
  id: number;
  filename: string;
  product_name: string | null;
  mrp: string | null;
  net_quantity: string | null;
  manufacturer: string | null;
  marketer: string | null;
  batch_number: string | null;
  manufacture_date: string | null;
  use_by_date: string | null;
  license_number: string | null;
  overall_status: string | null;
  risk_level: string | null;
  compliance_score: number | null;
  report_path: string | null;
  created_at: string;
}

const FIELD_LABELS: Record<
  keyof Pick<
    Analysis,
    | "product_name"
    | "mrp"
    | "net_quantity"
    | "manufacturer"
    | "marketer"
    | "batch_number"
    | "manufacture_date"
    | "use_by_date"
    | "license_number"
  >,
  string
> = {
  product_name: "Product name",
  mrp: "MRP",
  net_quantity: "Net quantity",
  manufacturer: "Manufacturer",
  marketer: "Marketer",
  batch_number: "Batch number",
  manufacture_date: "Manufacturing date",
  use_by_date: "Use-by date",
  license_number: "License number",
};

const FIELD_KEYS = Object.keys(
  FIELD_LABELS
) as Array<keyof typeof FIELD_LABELS>;

export default function ComplianceResult() {
  const navigate = useNavigate();
  const { id } = useParams();

  const [analysis, setAnalysis] =
    useState<Analysis | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) {
      setError("Analysis ID is missing.");
      setLoading(false);
      return;
    }

    loadAnalysis(id);
  }, [id]);

  async function loadAnalysis(analysisId: string) {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(
        `/history/${analysisId}`
      );

      setAnalysis(response.data);
    } catch (err: any) {
      console.error(
        "Failed to load analysis:",
        err
      );

      setError(
        err?.response?.data?.detail ||
          "Unable to load this analysis."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString);

    if (Number.isNaN(date.getTime())) {
      return "Unknown";
    }

    return date.toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function getStatus(
    value: string | null,
    score: number
  ) {
    const status =
      value?.toLowerCase() || "";

    if (
      status.includes("non") ||
      status.includes("fail") ||
      status.includes("violation")
    ) {
      return "Non-compliant";
    }

    if (
      status.includes("review") ||
      status.includes("warning") ||
      status.includes("partial")
    ) {
      return "Review";
    }

    if (
      status.includes("compliant") ||
      status.includes("pass")
    ) {
      return "Compliant";
    }

    if (score >= 90) return "Compliant";
    if (score >= 75) return "Review";

    return "Non-compliant";
  }

  function getStatusClass(
    status: string
  ) {
    if (status === "Compliant") {
      return "status-good";
    }

    if (status === "Review") {
      return "status-review";
    }

    return "status-danger";
  }

  function getFieldConfidence(
    value: string | null
  ) {
    return value ? 95 : 0;
  }

  if (loading) {
    return (
      <main className="result-page">
        <div className="dashboard-glow dashboard-glow-one" />
        <div className="dashboard-glow dashboard-glow-two" />

        <header className="dashboard-header">
          <div className="dashboard-brand">
            <div className="dashboard-brand-icon">
              <ScanLine size={20} />
            </div>

            <div>
              <strong>SmartLabel</strong>
              <span>AI</span>
            </div>
          </div>
        </header>

        <div className="result-content">
          <div className="history-empty">
            <div>
              <Clock3 size={22} />
            </div>

            <strong>
              Loading analysis...
            </strong>

            <p>
              Fetching the saved compliance result.
            </p>
          </div>
        </div>
      </main>
    );
  }

  if (error || !analysis) {
    return (
      <main className="result-page">
        <div className="dashboard-glow dashboard-glow-one" />
        <div className="dashboard-glow dashboard-glow-two" />

        <header className="dashboard-header">
          <div className="dashboard-brand">
            <div className="dashboard-brand-icon">
              <ScanLine size={20} />
            </div>

            <div>
              <strong>SmartLabel</strong>
              <span>AI</span>
            </div>
          </div>
        </header>

        <div className="result-content">
          <div className="history-empty">
            <div>
              <X size={22} />
            </div>

            <strong>
              Analysis unavailable
            </strong>

            <p>
              {error ||
                "The requested analysis could not be found."}
            </p>

            <button
              className="dashboard-upload-button"
              onClick={() =>
                navigate("/history")
              }
            >
              <ArrowLeft size={15} />
              Back to history
            </button>
          </div>
        </div>
      </main>
    );
  }

  const score = Math.round(
    analysis.compliance_score ?? 0
  );

  const status = getStatus(
    analysis.overall_status,
    score
  );

  const populatedFields = FIELD_KEYS.filter(
    (key) => analysis[key]
  );

  const missingFields = FIELD_KEYS.filter(
    (key) => !analysis[key]
  );

  return (
    <main className="result-page">
      {/* Background */}
      <div className="dashboard-glow dashboard-glow-one" />
      <div className="dashboard-glow dashboard-glow-two" />

      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <div className="dashboard-brand-icon">
            <ScanLine size={20} />
          </div>

          <div>
            <strong>SmartLabel</strong>
            <span>AI</span>
          </div>
        </div>

        <div className="dashboard-header-actions">
          <button
            className="result-history-button"
            onClick={() =>
              navigate("/history")
            }
          >
            <Clock3 size={15} />
            History
          </button>

          <div className="dashboard-avatar">
            A
          </div>
        </div>
      </header>

      <div className="result-content">
        {/* Breadcrumb */}
        <motion.div
          className="result-breadcrumb"
          initial={{
            opacity: 0,
            x: -10,
          }}
          animate={{
            opacity: 1,
            x: 0,
          }}
        >
          <button
            onClick={() =>
              navigate("/history")
            }
          >
            <ArrowLeft size={14} />
            Analysis history
          </button>

          <ChevronRight size={13} />

          <span>
            Analysis #{analysis.id}
          </span>
        </motion.div>

        {/* Heading */}
        <motion.section
          className="result-heading"
          initial={{
            opacity: 0,
            y: 15,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >
          <div>
            <div className="dashboard-eyebrow">
              <span />
              ANALYSIS COMPLETE
            </div>

            <h1>
              Compliance
              <span> result.</span>
            </h1>

            <p>
              {analysis.product_name ||
                "Unnamed product"}{" "}
              · analyzed{" "}
              {formatDate(analysis.created_at)}
            </p>
          </div>

          <div className="result-actions">
            <button
              className="result-secondary-button"
              onClick={() =>
                navigate("/analysis/new")
              }
            >
              <ScanLine size={16} />
              Analyze another
            </button>

            <button
              className="result-primary-button"
              disabled={!analysis.report_path}
              title={
                analysis.report_path
                  ? "Download report"
                  : "PDF report is not available yet"
              }
            >
              <Download size={16} />
              Download report
            </button>
          </div>
        </motion.section>

        {/* Score + source */}
        <section className="result-top-grid">
          {/* Score */}
          <motion.div
            className="result-score-card"
            initial={{
              opacity: 0,
              scale: 0.98,
            }}
            animate={{
              opacity: 1,
              scale: 1,
            }}
            transition={{
              duration: 0.5,
            }}
          >
            <div className="score-card-header">
              <div>
                <span className="card-kicker">
                  OVERALL COMPLIANCE
                </span>

                <h2>
                  {status === "Compliant"
                    ? "Strong compliance"
                    : status === "Review"
                      ? "Needs review"
                      : "Non-compliant"}
                </h2>
              </div>

              <div
                className={`result-status-badge ${getStatusClass(
                  status
                )}`}
              >
                {status === "Compliant" ? (
                  <CheckCircle2 size={15} />
                ) : (
                  <ShieldAlert size={15} />
                )}

                {status}
              </div>
            </div>

            <div className="score-main">
              <div className="score-ring">
                <svg
                  viewBox="0 0 160 160"
                  className="score-svg"
                >
                  <circle
                    cx="80"
                    cy="80"
                    r="67"
                    className="score-track"
                  />

                  <motion.circle
                    cx="80"
                    cy="80"
                    r="67"
                    className="score-progress"
                    initial={{
                      strokeDashoffset: 421,
                    }}
                    animate={{
                      strokeDashoffset:
                        421 -
                        (421 * score) / 100,
                    }}
                    transition={{
                      duration: 1.2,
                      ease: "easeOut",
                    }}
                  />
                </svg>

                <div className="score-number">
                  <strong>{score}</strong>
                  <span>/ 100</span>
                </div>
              </div>

              <div className="score-summary">
                <div className="score-summary-item">
                  <Check size={14} />
                  <span>
                    {populatedFields.length} fields
                    detected
                  </span>
                </div>

                <div className="score-summary-item">
                  {missingFields.length === 0 ? (
                    <Check size={14} />
                  ) : (
                    <TriangleAlert size={14} />
                  )}

                  <span>
                    {missingFields.length === 0
                      ? "No extracted fields missing"
                      : `${missingFields.length} fields need review`}
                  </span>
                </div>

                <div className="score-summary-item review">
                  <TriangleAlert size={14} />

                  <span>
                    Automated screening result
                  </span>
                </div>
              </div>
            </div>

            <div className="score-confidence">
              <span>
                Analysis confidence
              </span>

              <strong>
                {populatedFields.length > 0
                  ? "Based on extracted data"
                  : "Limited"}
              </strong>

              <div className="confidence-bar">
                <motion.i
                  initial={{
                    width: 0,
                  }}
                  animate={{
                    width: `${
                      populatedFields.length > 0
                        ? 90
                        : 25
                    }%`,
                  }}
                  transition={{
                    duration: 0.8,
                    delay: 0.3,
                  }}
                />
              </div>
            </div>
          </motion.div>

          {/* Source image */}
          <motion.div
            className="result-image-card"
            initial={{
              opacity: 0,
              y: 15,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.5,
              delay: 0.1,
            }}
          >
            <div className="result-image-header">
              <div>
                <span className="card-kicker">
                  SOURCE IMAGE
                </span>

                <h2>
                  {analysis.filename}
                </h2>
              </div>

              <button
                title="Source image"
                disabled
              >
                <ArrowUpRight size={15} />
              </button>
            </div>

            <div className="package-preview">
              <div className="package-mock">
                <div className="package-brand">
                  SMARTLABEL
                </div>

                <div className="package-title">
                  PRODUCT
                  <br />
                  LABEL
                </div>

                <div className="package-weight">
                  {analysis.net_quantity ||
                    "Net quantity"}
                </div>

                <div className="package-details">
                  <span>
                    {analysis.mrp || "MRP"}
                  </span>

                  <span>
                    {analysis.product_name ||
                      "Product"}
                  </span>
                </div>
              </div>
            </div>

            <div className="image-caption">
              <Info size={13} />
              Source-image preview and visual
              detection evidence will be connected
              in the visual-analysis stage.
            </div>
          </motion.div>
        </section>

        {/* Declarations */}
        <motion.section
          className="result-section-card"
          initial={{
            opacity: 0,
            y: 20,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.5,
            delay: 0.2,
          }}
        >
          <div className="result-section-header">
            <div>
              <span className="card-kicker">
                INFORMATION EXTRACTION
              </span>

              <h2>
                Detected declarations
              </h2>

              <p>
                Information extracted from the
                analyzed package image.
              </p>
            </div>

            <div className="declaration-count">
              <strong>
                {populatedFields.length}
              </strong>

              <span>
                fields detected
              </span>
            </div>
          </div>

          <div className="declaration-grid">
            {FIELD_KEYS.map(
              (key, index) => {
                const value =
                  analysis[key];

                const confidence =
                  getFieldConfidence(value);

                const passed =
                  Boolean(value);

                return (
                  <motion.div
                    key={key}
                    className="declaration-item"
                    initial={{
                      opacity: 0,
                      y: 8,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{
                      delay:
                        0.25 +
                        index * 0.05,
                    }}
                  >
                    <div className="declaration-icon">
                      {passed ? (
                        <CheckCircle2
                          size={16}
                        />
                      ) : (
                        <ShieldAlert
                          size={16}
                        />
                      )}
                    </div>

                    <div className="declaration-content">
                      <span>
                        {FIELD_LABELS[key]}
                      </span>

                      <strong>
                        {value ||
                          "Not detected"}
                      </strong>

                      <div className="declaration-confidence">
                        <span>
                          Extraction status
                        </span>

                        <strong>
                          {passed
                            ? `${confidence}%`
                            : "Review"}
                        </strong>
                      </div>
                    </div>

                    <div
                      className={`declaration-status ${
                        passed
                          ? "declaration-pass"
                          : "declaration-review"
                      }`}
                    >
                      {passed
                        ? "Detected"
                        : "Missing"}
                    </div>
                  </motion.div>
                );
              }
            )}
          </div>
        </motion.section>

        {/* Findings */}
        <section className="result-bottom-grid">
          <motion.div
            className="findings-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.5,
              delay: 0.3,
            }}
          >
            <div className="result-section-header compact">
              <div>
                <span className="card-kicker">
                  COMPLIANCE ENGINE
                </span>

                <h2>
                  Findings & recommendations
                </h2>
              </div>

              <ShieldCheck size={20} />
            </div>

            <div className="findings-list">
              {missingFields.length ===
              0 ? (
                <div className="finding-item">
                  <div className="finding-icon finding-low">
                    <CheckCircle2 size={17} />
                  </div>

                  <div className="finding-content">
                    <div className="finding-title-row">
                      <strong>
                        No missing extracted
                        fields
                      </strong>

                      <span>
                        passed
                      </span>
                    </div>

                    <p>
                      All fields currently
                      stored by SmartLabel AI
                      were detected in the
                      analysis result.
                    </p>

                    <small>
                      Further category-specific
                      regulatory checks will be
                      added to the compliance
                      engine.
                    </small>
                  </div>
                </div>
              ) : (
                missingFields.map(
                  (key) => (
                    <div
                      className="finding-item"
                      key={key}
                    >
                      <div className="finding-icon finding-medium">
                        <TriangleAlert
                          size={17}
                        />
                      </div>

                      <div className="finding-content">
                        <div className="finding-title-row">
                          <strong>
                            {FIELD_LABELS[
                              key
                            ]}{" "}
                            not detected
                          </strong>

                          <span>
                            review
                          </span>
                        </div>

                        <p>
                          This declaration was
                          not found in the
                          stored extraction
                          result and should be
                          manually verified on
                          the package.
                        </p>

                        <small>
                          Automated screening
                          finding
                        </small>
                      </div>
                    </div>
                  )
                )
              )}
            </div>
          </motion.div>

          {/* Summary */}
          <motion.div
            className="summary-card"
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              duration: 0.5,
              delay: 0.4,
            }}
          >
            <span className="card-kicker">
              SCREENING SUMMARY
            </span>

            <h2>
              {status === "Compliant"
                ? "Ready for review"
                : "Manual review recommended"}
            </h2>

            <p>
              SmartLabel AI has completed an
              automated screening of this saved
              analysis. Regulatory decisions should
              not rely solely on this automated
              result.
            </p>

            <div className="summary-stat">
              <div>
                <span>
                  Detected
                </span>

                <strong>
                  {populatedFields.length}
                </strong>
              </div>

              <div>
                <span>
                  Missing
                </span>

                <strong>
                  {missingFields.length}
                </strong>
              </div>

              <div>
                <span>
                  Score
                </span>

                <strong>
                  {score}
                </strong>
              </div>
            </div>

            <div className="summary-note">
              <ShieldCheck size={16} />

              <span>
                Automated screening only — final
                regulatory assessment should be
                performed by an authorized reviewer.
              </span>
            </div>
          </motion.div>
        </section>

        {/* Bottom */}
        <motion.div
          className="result-footer"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            delay: 0.55,
          }}
        >
          <button
            className="result-secondary-button"
            onClick={() =>
              navigate("/history")
            }
          >
            <ArrowLeft size={15} />
            Back to repository
          </button>

          <button
            className="result-primary-button"
            disabled={!analysis.report_path}
          >
            <Download size={16} />
            Generate PDF report
          </button>
        </motion.div>
      </div>
    </main>
  );
}