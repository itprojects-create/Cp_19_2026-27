import { useEffect, useMemo, useState } from "react";
import { createSession } from "../lib/api";

type Identity = {
  businessName: string;
  ownerName: string;
  cityArea: string;
  businessType: string;
};

export function useApplySession() {
  const [step, setStep] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [identity, setIdentity] = useState<Identity>({
    businessName: "",
    ownerName: "",
    cityArea: "",
    businessType: "",
  });

  useEffect(() => {
    const existing = sessionStorage.getItem("shadow_credit_session_id");
    if (existing) setSessionId(existing);
  }, []);

  function next() {
    setStep((s) => Math.min(5, s + 1));
  }

  function back() {
    setStep((s) => Math.max(1, s - 1));
  }

  async function ensureSession() {
    if (sessionId) return sessionId;
    const res = await createSession({
      owner_name: identity.ownerName,
      location_district: identity.cityArea,
      consent_given: true,
      demo_mode: false,
    });
    const id = res?.data?.session_id as string;
    setSessionId(id);
    sessionStorage.setItem("shadow_credit_session_id", id);
    return id;
  }

  const canContinueIdentity = useMemo(
    () => Boolean(identity.businessName && identity.ownerName && identity.cityArea && identity.businessType),
    [identity],
  );

  return {
    step,
    setStep,
    next,
    back,
    sessionId,
    identity,
    setIdentity,
    canContinueIdentity,
    ensureSession,
  };
}

