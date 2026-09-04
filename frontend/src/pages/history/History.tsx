import { motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  FileText,
  Filter,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";
import api from "../../services/api";

interface Analysis {
  id: number;
  filename: string;
  product_name: string | null;
  overall_status: string | null;
  risk_level: string | null;
  compliance_score: number | null;
  created_at: string;
}

type StatusFilter =
  | "All"
  | "Compliant"
  | "Review"
  | "Non-compliant";

export default function History() {
  const navigate = useNavigate();

  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] =
    useState<StatusFilter>("All");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/history/");

      setAnalyses(response.data.history ?? []);
    } catch (err: any) {
      console.error("Failed to load history:", err);

      setError(
        err?.response?.data?.detail ||
          "Unable to load analysis history."
      );
    } finally {
      setLoading(false);
    }
  }

  function getStatus(
    analysis: Analysis
  ): StatusFilter {
    const status =
      analysis.overall_status?.toLowerCase() || "";

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

    // Fallback based on score
    const score = analysis.compliance_score ?? 0;

    if (score >= 90) return "Compliant";
    if (score >= 75) return "Review";

    return "Non-compliant";
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

  const filteredAnalyses = useMemo(() => {
    const query = search.trim().toLowerCase();

    return analyses.filter((analysis) => {
      const productName =
        analysis.product_name || "";

      const filename =
        analysis.filename || "";

      const matchesSearch =
        !query ||
        productName.toLowerCase().includes(query) ||
        filename.toLowerCase().includes(query);

      const status = getStatus(analysis);

      const matchesFilter =
        filter === "All" ||
        status === filter;

      return matchesSearch && matchesFilter;
    });
  }, [analyses, search, filter]);

  function getStatusIcon(status: StatusFilter) {
    if (status === "Compliant") {
      return <CheckCircle2 size={16} />;
    }

    if (status === "Review") {
      return <ShieldAlert size={16} />;
    }

    return <XCircle size={16} />;
  }

  function getScoreClass(score: number) {
    if (score >= 90) {
      return "score-good";
    }

    if (score >= 75) {
      return "score-review";
    }

    return "score-danger";
  }

  return (
    <main className="history-page">
      {/* Background */}
      <div className="dashboard-glow dashboard-glow-one" />
      <div className="dashboard-glow dashboard-glow-two" />

      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-brand">
          <div className="dashboard-brand-icon">
            <FileText size={20} />
          </div>

          <div>
            <strong>SmartLabel</strong>
            <span>AI</span>
          </div>
        </div>

        <button
          className="dashboard-avatar"
          onClick={() => navigate("/dashboard")}
          title="Back to dashboard"
        >
          A
        </button>
      </header>

      <div className="history-content">
        {/* Top */}
        <motion.section
          className="history-top"
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
            <button
              className="history-back"
              onClick={() =>
                navigate("/dashboard")
              }
            >
              <ArrowLeft size={15} />
              Dashboard
            </button>

            <div className="dashboard-eyebrow">
              <span />
              ANALYSIS REPOSITORY
            </div>

            <h1>
              Analysis
              <span> history.</span>
            </h1>

            <p>
              Review previously analyzed product
              labels, compliance scores and detected
              issues.
            </p>
          </div>

          <button
            className="dashboard-upload-button"
            onClick={() =>
              navigate("/analysis/new")
            }
          >
            <FileText size={17} />
            New analysis
          </button>
        </motion.section>

        {/* Repository */}
        <motion.section
          className="history-card"
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
            delay: 0.1,
          }}
        >
          {/* Toolbar */}
          <div className="history-toolbar">
            <div className="history-search">
              <Search size={17} />

              <input
                type="text"
                placeholder="Search by product or filename..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />

              {search && (
                <button
                  onClick={() => setSearch("")}
                  aria-label="Clear search"
                >
                  <XCircle size={16} />
                </button>
              )}
            </div>

            <div className="history-filters">
              <div className="filter-label">
                <Filter size={14} />
                Status
              </div>

              <div className="filter-buttons">
                {(
                  [
                    "All",
                    "Compliant",
                    "Review",
                    "Non-compliant",
                  ] as const
                ).map((item) => (
                  <button
                    key={item}
                    className={
                      filter === item
                        ? "active"
                        : ""
                    }
                    onClick={() =>
                      setFilter(item)
                    }
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Result count */}
          <div className="history-result-bar">
            <div>
              <SlidersHorizontal size={14} />

              <span>
                {filteredAnalyses.length}{" "}
                {filteredAnalyses.length === 1
                  ? "analysis"
                  : "analyses"}
              </span>
            </div>

            <span>
              {analyses.length > 0
                ? "Showing your analysis history"
                : "No analysis records yet"}
            </span>
          </div>

          {/* Loading */}
          {loading && (
            <div className="history-empty">
              <div>
                <Clock3 size={22} />
              </div>

              <strong>
                Loading analysis history...
              </strong>

              <p>
                Fetching your previous label
                analyses.
              </p>
            </div>
          )}

          {/* Error */}
          {!loading && error && (
            <div className="history-empty">
              <div>
                <XCircle size={22} />
              </div>

              <strong>
                Unable to load history
              </strong>

              <p>{error}</p>

              <button
                className="dashboard-upload-button"
                onClick={loadHistory}
              >
                Try again
              </button>
            </div>
          )}

          {/* Empty database */}
          {!loading &&
            !error &&
            analyses.length === 0 && (
              <div className="history-empty">
                <div>
                  <FileText size={22} />
                </div>

                <strong>
                  No analyses yet
                </strong>

                <p>
                  Upload a product label to create
                  your first compliance analysis.
                </p>

                <button
                  className="dashboard-upload-button"
                  onClick={() =>
                    navigate("/analysis/new")
                  }
                >
                  Start analysis
                </button>
              </div>
            )}

          {/* No filtered results */}
          {!loading &&
            !error &&
            analyses.length > 0 &&
            filteredAnalyses.length === 0 && (
              <div className="history-empty">
                <div>
                  <Search size={22} />
                </div>

                <strong>
                  No analyses found
                </strong>

                <p>
                  Try another search or change the
                  status filter.
                </p>
              </div>
            )}

          {/* Table */}
          {!loading &&
            !error &&
            filteredAnalyses.length > 0 && (
              <div className="history-table">
                <div className="history-table-header">
                  <span>Analysis</span>
                  <span>Score</span>
                  <span>Status</span>
                  <span>Analyzed</span>
                  <span />
                </div>

                {filteredAnalyses.map(
                  (analysis, index) => {
                    const status =
                      getStatus(analysis);

                    const score =
                      analysis.compliance_score ??
                      0;

                    const name =
                      analysis.product_name ||
                      "Unnamed product";

                    return (
                      <motion.div
                        key={analysis.id}
                        className="history-row"
                        initial={{
                          opacity: 0,
                          y: 8,
                        }}
                        animate={{
                          opacity: 1,
                          y: 0,
                        }}
                        transition={{
                          delay: index * 0.04,
                        }}
                        whileHover={{
                          x: 3,
                        }}
                        onClick={() =>
                          navigate(
                            `/analysis/${analysis.id}`
                          )
                        }
                      >
                        <div className="history-analysis">
                          <div className="history-file-icon">
                            <FileText size={17} />
                          </div>

                          <div>
                            <strong>
                              {name}
                            </strong>

                            <span>
                              {analysis.filename}
                            </span>
                          </div>
                        </div>

                        <div
                          className={`history-score ${getScoreClass(
                            score
                          )}`}
                        >
                          {Math.round(score)}%
                        </div>

                        <div
                          className={`history-status ${
                            status ===
                            "Compliant"
                              ? "status-good"
                              : status ===
                                  "Review"
                                ? "status-review"
                                : "status-danger"
                          }`}
                        >
                          {getStatusIcon(status)}
                          {status}
                        </div>

                        <div className="history-date">
                          <Clock3 size={13} />
                          {formatDate(
                            analysis.created_at
                          )}
                        </div>

                        <button
                          className="history-open"
                          onClick={(event) => {
                            event.stopPropagation();

                            navigate(
                              `/analysis/${analysis.id}`
                            );
                          }}
                          aria-label={`Open ${name}`}
                        >
                          <ArrowUpRight
                            size={16}
                          />
                        </button>
                      </motion.div>
                    );
                  }
                )}
              </div>
            )}
        </motion.section>

        {/* Footer insight */}
        <motion.div
          className="history-insight"
          initial={{
            opacity: 0,
          }}
          animate={{
            opacity: 1,
          }}
          transition={{
            delay: 0.35,
          }}
        >
          <ShieldAlert size={17} />

          <span>
            Compliance results are automated
            screening results and should be reviewed
            before making regulatory decisions.
          </span>
        </motion.div>
      </div>
    </main>
  );
}