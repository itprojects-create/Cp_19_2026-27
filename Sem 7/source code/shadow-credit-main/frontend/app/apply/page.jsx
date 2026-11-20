'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import ApplyShell from '@/components/layout/ApplyShell';
import StepDots from '@/components/apply/StepDots';
import Step1Identity, { derivePersonaKey } from '@/components/apply/Step1Identity';
import Step2WhatsApp from '@/components/apply/Step2WhatsApp';
import Step3UPI from '@/components/apply/Step3UPI';
import Step4Bill from '@/components/apply/Step4Bill';
import Step5Consent from '@/components/apply/Step5Consent';
import styles from './page.module.css';

const TOTAL_STEPS = 5;

export default function ApplyPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [direction, setDirection] = useState('forward');

  // Session data accumulated across steps
  const [sessionData, setSessionData] = useState({
    sessionId: null,
    ownerName: '',
    businessType: '',
    locationDistrict: '',
    persona: '',          // populated by Step1 after derivePersonaKey()
    whatsappUploaded: false,
    upiCount: 0,
    billUploaded: false,
  });

  function advanceStep(newData = {}) {
    setSessionData((prev) => ({ ...prev, ...newData }));
    setDirection('forward');
    setCurrentStep((s) => Math.min(s + 1, TOTAL_STEPS));
  }

  function retreatStep() {
    setDirection('backward');
    setCurrentStep((s) => Math.max(s - 1, 1));
  }

  function redirectToProcessing(sessionId) {
    // Prefer the persona key already derived and stored in sessionData by Step1.
    // If for any reason it's missing (e.g. page refresh), re-derive from businessType.
    // This means the URL ALWAYS has ?persona=<valid key> — never blank.
    const personaKey =
      sessionData.persona ||
      derivePersonaKey(sessionData.businessType);

    if (!personaKey || !['meena', 'suresh', 'raju'].includes(personaKey)) {
      // This should never happen — log loudly so it can't hide.
      console.error(
        '[Shadow Credit] redirectToProcessing: Could not determine persona key!',
        { sessionData, personaKey }
      );
    }

    router.push(`/apply/agents?session=${sessionId}&persona=${personaKey}`);
  }

  // Each step receives: sessionData, onNext(newData), onBack
  function renderStep() {
    switch (currentStep) {
      case 1:
        return (
          <Step1Identity
            onNext={advanceStep}
            sessionData={sessionData}
          />
        );
      case 2:
        return (
          <Step2WhatsApp
            onNext={advanceStep}
            onBack={retreatStep}
            sessionData={sessionData}
          />
        );
      case 3:
        return (
          <Step3UPI
            onNext={advanceStep}
            onBack={retreatStep}
            sessionData={sessionData}
          />
        );
      case 4:
        return (
          <Step4Bill
            onNext={advanceStep}
            onBack={retreatStep}
            sessionData={sessionData}
          />
        );
      case 5:
        return (
          <Step5Consent
            onBack={retreatStep}
            sessionData={sessionData}
            onRedirect={redirectToProcessing}
          />
        );
      default:
        return null;
    }
  }

  return (
    <ApplyShell showBack={currentStep === 1} backHref="/">
      <div className={styles.container}>

        {/* Step progress dots */}
        <StepDots total={TOTAL_STEPS} current={currentStep} />

        {/* Step content with slide transition */}
        <div
          className={`${styles.stepWrapper} ${
            direction === 'forward'
              ? styles.slideInRight
              : styles.slideInLeft
          }`}
          key={currentStep}
        >
          {renderStep()}
        </div>

      </div>
    </ApplyShell>
  );
}
