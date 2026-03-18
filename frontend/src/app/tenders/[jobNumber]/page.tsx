"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { TopBar } from "@/components/top-bar";
import { nxApi, type NxTender } from "@/lib/nexus-api";
import {
  ArrowLeft,
  Calendar,
  ExternalLink,
  Phone,
  Mail,
  User,
  Loader2,
  Download,
  FileText,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function TenderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobNumber = decodeURIComponent(params.jobNumber as string);

  const [tender, setTender] = useState<NxTender | null>(null);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState<string | null>(null);

  const loadTender = useCallback(async () => {
    try {
      const data = await nxApi.tenders.get(jobNumber);
      setTender(data);
    } catch {
      setTender(null);
    } finally {
      setLoading(false);
    }
  }, [jobNumber]);

  useEffect(() => {
    loadTender();
  }, [loadTender]);

  async function handleEnrich() {
    setEnriching(true);
    setEnrichMsg(null);
    try {
      const result = await nxApi.tenders.enrich(jobNumber);
      setEnrichMsg(
        result.sections_added > 0
          ? `已新增 ${result.sections_added} 個區段（投標須知 ${result.notice_doc_len} 字）`
          : "此標案已有完整內容"
      );
      await loadTender();
    } catch (err) {
      setEnrichMsg(`擷取失敗: ${err}`);
    } finally {
      setEnriching(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-slate-400" size={32} />
      </div>
    );
  }

  if (!tender) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-slate-500">找不到標案 {jobNumber}</p>
        <button onClick={() => router.back()} className="text-blue-500 text-sm">
          返回
        </button>
      </div>
    );
  }

  // Parse body_md into sections
  const sections = parseSections(tender.body_md || "");

  return (
    <div className="flex flex-col h-full">
      <TopBar title="標案詳情">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
        >
          <ArrowLeft size={14} />
          返回
        </button>
      </TopBar>

      <div className="flex-1 overflow-auto px-4 lg:px-6 py-4">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Header */}
          <div>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-lg font-bold text-slate-900 dark:text-slate-50 leading-snug">
                  {tender.name}
                </h1>
                <p className="text-sm text-slate-500 mt-1">{tender.agency}</p>
              </div>
              {tender.days_left !== null && (
                <DaysLeftBadgeLarge days={tender.days_left} />
              )}
            </div>

            {/* Quick info chips */}
            <div className="flex flex-wrap gap-2 mt-3">
              <Chip label={tender.category_detail || tender.category} />
              <Chip label={tender.tender_type} />
              {tender.budget_amount && <Chip label={tender.budget_amount} accent />}
            </div>
          </div>

          {/* Info grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InfoCard icon={Calendar} label="截止投標" value={tender.deadline || "未定"} />
            <InfoCard icon={FileText} label="案號" value={tender.job_number} />
            {tender.contact_name && (
              <InfoCard icon={User} label="聯絡人" value={tender.contact_name} />
            )}
            {tender.contact_phone && (
              <InfoCard icon={Phone} label="電話" value={tender.contact_phone} />
            )}
            {tender.contact_email && (
              <InfoCard icon={Mail} label="Email" value={tender.contact_email} />
            )}
            {tender.reference_url && (
              <a
                href={tender.reference_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700 hover:border-blue-400 transition-colors group"
              >
                <ExternalLink size={16} className="text-slate-400 group-hover:text-blue-500" />
                <div>
                  <p className="text-[11px] text-slate-400">外部連結</p>
                  <p className="text-xs text-blue-500 group-hover:underline">g0v 採購資料</p>
                </div>
              </a>
            )}
          </div>

          {/* Tags */}
          {tender.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {tender.tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Enrich button */}
          {!tender.has_notice && (
            <div className="border border-dashed border-slate-300 dark:border-slate-600 rounded-xl p-4 text-center">
              <p className="text-sm text-slate-500 mb-3">
                此標案尚未擷取完整內文（投標須知、資格要求等）
              </p>
              <button
                onClick={handleEnrich}
                disabled={enriching}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {enriching ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Download size={14} />
                )}
                從政府採購網擷取內文
              </button>
              {enrichMsg && (
                <p className="mt-2 text-xs text-slate-500">{enrichMsg}</p>
              )}
            </div>
          )}

          {/* Body content sections */}
          {sections.map((section, i) => (
            <BodySection key={i} heading={section.heading} content={section.content} />
          ))}
        </div>
      </div>
    </div>
  );
}

// --- Helper components ---

function DaysLeftBadgeLarge({ days }: { days: number }) {
  const color =
    days <= 7
      ? "bg-red-500 text-white"
      : days <= 14
        ? "bg-orange-500/15 text-orange-600"
        : "bg-green-500/10 text-green-600";
  const label = days === 0 ? "今天截止" : days < 0 ? "已截止" : `剩 ${days} 天`;
  return (
    <span className={`text-sm px-3 py-1 rounded-lg font-bold ${color}`}>
      {label}
    </span>
  );
}

function Chip({ label, accent }: { label: string; accent?: boolean }) {
  return (
    <span
      className={`text-xs px-2.5 py-1 rounded-full ${
        accent
          ? "bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium"
          : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
      }`}
    >
      {label}
    </span>
  );
}

function InfoCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Calendar;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
      <Icon size={16} className="text-slate-400 flex-shrink-0" />
      <div>
        <p className="text-[11px] text-slate-400">{label}</p>
        <p className="text-sm text-slate-900 dark:text-slate-100">{value}</p>
      </div>
    </div>
  );
}

// --- Body section with markdown rendering and collapse ---

function BodySection({ heading, content }: { heading: string; content: string }) {
  const isLong = content.length > 1500;
  const [expanded, setExpanded] = useState(!isLong);
  const isNotice = heading === "投標須知";

  const displayContent = expanded ? content : content.slice(0, 1500) + "...";

  return (
    <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
      {heading && (
        <div
          className={`px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
            isNotice ? "bg-blue-50/50 dark:bg-blue-900/10" : "bg-slate-50 dark:bg-slate-800/30"
          }`}
          onClick={() => isLong && setExpanded(!expanded)}
        >
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-50">
            {heading}
          </h2>
          {isLong && (
            expanded
              ? <ChevronUp size={16} className="text-slate-400" />
              : <ChevronDown size={16} className="text-slate-400" />
          )}
        </div>
      )}
      <div className="px-4 py-3">
        <div className="prose dark:prose-invert prose-sm max-w-none prose-table:text-xs prose-th:bg-slate-100 dark:prose-th:bg-slate-800 prose-th:px-3 prose-th:py-1.5 prose-td:px-3 prose-td:py-1.5 prose-td:border-slate-200 dark:prose-td:border-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
        </div>
        {isLong && !expanded && (
          <button
            onClick={() => setExpanded(true)}
            className="mt-2 text-xs text-blue-500 hover:text-blue-600"
          >
            顯示全部內容
          </button>
        )}
      </div>
    </div>
  );
}

// --- Parse markdown body into sections ---

interface Section {
  heading: string;
  content: string;
}

function parseSections(body: string): Section[] {
  if (!body.trim()) return [];

  const lines = body.split("\n");
  const sections: Section[] = [];
  let currentHeading = "";
  let currentLines: string[] = [];

  for (const line of lines) {
    const headingMatch = line.match(/^#{1,3}\s+(.+)/);
    if (headingMatch) {
      // Save previous section
      if (currentHeading || currentLines.length > 0) {
        const content = currentLines.join("\n").trim();
        if (content) {
          sections.push({ heading: currentHeading, content });
        }
      }
      currentHeading = headingMatch[1];
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }

  // Save last section
  if (currentHeading || currentLines.length > 0) {
    const content = currentLines.join("\n").trim();
    if (content) {
      sections.push({ heading: currentHeading, content });
    }
  }

  return sections;
}
