"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import type {
  ConfidenceCalibrationResponse,
  HandoutResponse,
  SelfAssessmentResponse,
} from "@ticdss/shared-types";
import { useAuthStore } from "@/lib/authStore";
import {
  fetchHandout,
  regenerateHandout,
  submitConfidencePrediction,
  submitSelfAssessment,
} from "@/lib/handout";
import { HandoutHeader } from "@/components/handout/HandoutHeader";
import { RadarChartCard } from "@/components/handout/RadarChartCard";
import { ConfidenceCalibrationCard } from "@/components/handout/ConfidenceCalibrationCard";
import { StudyNotesCard } from "@/components/handout/StudyNotesCard";
import { MindMap } from "@/components/handout/MindMap";
import { HrvCurveCard } from "@/components/handout/HrvCurveCard";
import { FlowCurveCard } from "@/components/handout/FlowCurveCard";
import { DiscussionPromptsCard } from "@/components/handout/DiscussionPromptsCard";
import { SpacedRepetitionCard } from "@/components/handout/SpacedRepetitionCard";
import { SelfAssessmentForm } from "@/components/handout/SelfAssessmentForm";
import { AnnotatedTranscriptCard } from "@/components/handout/AnnotatedTranscriptCard";

const stagger = (i: number) => ({
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { delay: 0.05 + i * 0.05, duration: 0.3, ease: "easeOut" as const },
});

export default function HandoutPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params?.sessionId ?? "";
  const role = useAuthStore((s) => s.role);

  const [data, setData] = useState<HandoutResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [confidence, setConfidence] = useState<ConfidenceCalibrationResponse | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    fetchHandout(sessionId)
      .then((d) => {
        setData(d);
        setConfidence(d.confidence);
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  const handleRegenerate = async () => {
    toast.loading("重新生成講義中…", { id: "regen" });
    try {
      await regenerateHandout(sessionId);
      const fresh = await fetchHandout(sessionId);
      setData(fresh);
      setConfidence(fresh.confidence);
      toast.success("講義已重新生成", { id: "regen" });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "重新生成失敗";
      toast.error(msg, { id: "regen" });
    }
  };

  const handleDownloadPdf = () => {
    if (typeof window !== "undefined") window.print();
  };

  const handleConfidence = async (predicted: number) => {
    const r = await submitConfidencePrediction(sessionId, predicted);
    setConfidence(r);
  };

  const handleSelfAssessment = async (payload: SelfAssessmentResponse) => {
    await submitSelfAssessment(sessionId, payload);
    setData((prev) => (prev ? { ...prev, selfAssessment: payload } : prev));
  };

  if (loading || !data || !confidence) {
    return (
      <div className="max-w-3xl mx-auto py-24 text-center">
        <Loader2 size={32} className="animate-spin text-brand-500 mx-auto mb-4" />
        <p className="text-sm text-ink-muted">載入個人講義中…</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-6 lg:py-10 px-4 lg:px-6 handout-page">
      <HandoutHeader
        caseTitle={data.caseTitle}
        caseCode={data.caseCode}
        mode={data.mode}
        completedAt={data.completedAt}
        totalScore={data.totalScore}
        isAdmin={role === "admin"}
        onRegenerate={handleRegenerate}
        onDownloadPdf={handleDownloadPdf}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div {...stagger(0)} className="lg:col-span-1">
          <RadarChartCard points={data.radar} />
        </motion.div>

        <motion.div {...stagger(1)} className="lg:col-span-1">
          <ConfidenceCalibrationCard data={confidence} onSubmit={handleConfidence} />
        </motion.div>

        <motion.div {...stagger(2)} className="lg:col-span-2">
          <StudyNotesCard sections={data.studyNotes} />
        </motion.div>

        <motion.div {...stagger(3)} className="lg:col-span-2">
          <MindMap nodes={data.mindmap} />
        </motion.div>

        <motion.div {...stagger(4)} className="lg:col-span-2">
          <HrvCurveCard data={data.hrv} phaseBoundaries={data.phaseBoundaries} />
        </motion.div>

        <motion.div {...stagger(5)} className="lg:col-span-2">
          <FlowCurveCard data={data.flow} />
        </motion.div>

        <motion.div {...stagger(6)} className="lg:col-span-1">
          <DiscussionPromptsCard sessionId={sessionId} prompts={data.discussion} />
        </motion.div>

        <motion.div {...stagger(7)} className="lg:col-span-1">
          <SpacedRepetitionCard items={data.spacedRepetition} caseTitle={data.caseTitle} />
        </motion.div>

        <motion.div {...stagger(8)} className="lg:col-span-2">
          <SelfAssessmentForm
            sessionId={sessionId}
            initial={data.selfAssessment}
            onSubmit={handleSelfAssessment}
          />
        </motion.div>

        <motion.div {...stagger(9)} className="lg:col-span-2">
          <AnnotatedTranscriptCard sessionId={sessionId} />
        </motion.div>
      </div>

      <style jsx global>{`
        @media print {
          body {
            background: #ffffff !important;
          }
          .handout-page {
            max-width: 100% !important;
            padding: 0 !important;
          }
          aside,
          nav,
          .print\\:hidden {
            display: none !important;
          }
          section {
            break-inside: avoid;
            page-break-inside: avoid;
            box-shadow: none !important;
            border-color: #d7ccc8 !important;
          }
          button {
            display: none !important;
          }
          .handout-page section {
            margin-bottom: 12px !important;
          }
          * {
            animation: none !important;
            transition: none !important;
          }
        }
      `}</style>
    </div>
  );
}
