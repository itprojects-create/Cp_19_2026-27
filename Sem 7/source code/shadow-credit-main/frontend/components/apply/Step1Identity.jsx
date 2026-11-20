'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import styles from './Step1Identity.module.css';

const BUSINESS_TYPES = [
  'Kirana / General Store',
  'Tailor / Stitching Shop',
  'Vegetable / Fruit Vendor',
  'Medical / Pharmacy',
  'Tea Stall / Canteen',
  'Electronics Repair',
  'Hardware / Tools',
  'Salon / Beauty Parlour',
  'Auto / Transport',
  'Other Business',
];

// ── Persona key derivation ─────────────────────────────────────────────────
// This is a demo app with 3 fixed personas. We assign the persona key
// deterministically from business type so the routing is EXPLICIT and never
// silently falls back to 'meena'.
//
// Mapping:
//   suresh → Kirana / General Store   (Mahadev Enterprises)
//   meena  → Tailor / Stitching Shop  (Meena Fashion House)
//   raju   → everything else          (Raju Tent & Decoration)
//
// If you add a real 4th persona later, extend this function and add a new
// entry to PERSONAS in AgentsContent.jsx.
export function derivePersonaKey(businessType) {
  if (!businessType) return 'meena'; // safe default only used here
  const t = businessType.toLowerCase();
  if (t.includes('kirana') || t.includes('general store')) return 'suresh';
  if (t.includes('tailor') || t.includes('stitching')) return 'meena';
  // Tent/Event, Vegetable, Pharmacy, Tea Stall, Electronics, Hardware,
  // Salon, Auto, Other → raju (seasonal/mixed business dataset)
  return 'raju';
}

const EMPTY_ERRORS = {
  shopName:      '',
  ownerName:     '',
  location:      '',
  businessType:  '',
  api:           '',
};

export default function Step1Identity({ onNext, sessionData }) {
  const [form, setForm] = useState({
    shopName:     sessionData?.shopName     || '',
    ownerName:    sessionData?.ownerName    || '',
    location:     sessionData?.locationDistrict || '',
    businessType: sessionData?.businessType || '',
  });

  const [errors,  setErrors]  = useState(EMPTY_ERRORS);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState({});

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  }

  function handleBlur(field) {
    setTouched((prev) => ({ ...prev, [field]: true }));
    validateField(field, form[field]);
  }

  function validateField(field, value) {
    let message = '';
    if (field === 'shopName' && !value.trim()) {
      message = 'Shop name is required.';
    }
    if (field === 'ownerName' && !value.trim()) {
      message = 'Your name is required.';
    }
    if (field === 'location' && !value.trim()) {
      message = 'City and area is required.';
    }
    if (field === 'businessType' && !value) {
      message = 'Please select a business type.';
    }
    setErrors((prev) => ({ ...prev, [field]: message }));
    return message === '';
  }

  function validateAll() {
    const fields = ['shopName', 'ownerName', 'location', 'businessType'];
    const allTouched = fields.reduce((acc, f) => ({ ...acc, [f]: true }), {});
    setTouched(allTouched);

    let valid = true;
    const newErrors = { ...EMPTY_ERRORS };
    if (!form.shopName.trim()) {
      newErrors.shopName = 'Shop name is required.';
      valid = false;
    }
    if (!form.ownerName.trim()) {
      newErrors.ownerName = 'Your name is required.';
      valid = false;
    }
    if (!form.location.trim()) {
      newErrors.location = 'City and area is required.';
      valid = false;
    }
    if (!form.businessType) {
      newErrors.businessType = 'Please select a business type.';
      valid = false;
    }
    setErrors(newErrors);
    return valid;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validateAll()) return;

    setLoading(true);
    setErrors((prev) => ({ ...prev, api: '' }));

    try {
      const data = await api.createSession({
        owner_name:        `${form.ownerName} — ${form.shopName}`,
        location_district: form.location,
        business_type:     form.businessType,
        consent_given:     true,
        demo_mode:         false,
      });

      localStorage.setItem('sc_session_id',    data.session_id);
      localStorage.setItem('sc_owner_name',    form.ownerName);
      localStorage.setItem('sc_shop_name',     form.shopName);
      localStorage.setItem('sc_business_type', form.businessType);
      localStorage.setItem('sc_location',      form.location);
      // Derive the persona key NOW, while we have all identity data.
      // This is the single source of truth — every downstream page reads it
      // either from the URL param or from sessionStorage.
      const personaKey = derivePersonaKey(form.businessType);

      sessionStorage.setItem(
        'shadowcredit_session',
        JSON.stringify({
          businessName: form.shopName,
          cityArea: form.location,
          businessType: form.businessType,
          ownerName: form.ownerName,
          persona: personaKey, // explicit — never left blank
        })
      );

      onNext({
        sessionId:        data.session_id,
        ownerName:        form.ownerName,
        shopName:         form.shopName,
        businessType:     form.businessType,
        locationDistrict: form.location,
        persona:          personaKey, // pass forward so apply/page.jsx can use it
      });

    } catch (err) {
      setErrors((prev) => ({
        ...prev,
        api: err.message || 'Something went wrong. Please try again.',
      }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.step}>

      <div className={styles.heading}>
        <h2 className={styles.title}>Tell us about your business</h2>
        <p className={styles.subtitle}>
          This takes 30 seconds. Your information is protected under
          India's DPDP Act 2023 and never shared without your consent.
        </p>
      </div>

      <form onSubmit={handleSubmit} className={styles.form} noValidate>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="shopName">
            Dukaan ka naam
            <span className={styles.labelEn}> / Shop Name</span>
          </label>
          <input
            id="shopName"
            type="text"
            className={`${styles.input} ${
              errors.shopName && touched.shopName ? styles.inputError : ''
            }`}
            placeholder="e.g. Sharma General Store"
            value={form.shopName}
            onChange={(e) => handleChange('shopName', e.target.value)}
            onBlur={() => handleBlur('shopName')}
            disabled={loading}
            autoComplete="organization"
            autoFocus
          />
          {errors.shopName && touched.shopName && (
            <span className={styles.errorMsg}>{errors.shopName}</span>
          )}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="ownerName">
            Aapka naam
            <span className={styles.labelEn}> / Your Full Name</span>
          </label>
          <input
            id="ownerName"
            type="text"
            className={`${styles.input} ${
              errors.ownerName && touched.ownerName ? styles.inputError : ''
            }`}
            placeholder="e.g. Rajesh Kumar"
            value={form.ownerName}
            onChange={(e) => handleChange('ownerName', e.target.value)}
            onBlur={() => handleBlur('ownerName')}
            disabled={loading}
            autoComplete="name"
          />
          {errors.ownerName && touched.ownerName && (
            <span className={styles.errorMsg}>{errors.ownerName}</span>
          )}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="location">
            Sheher aur ilaka
            <span className={styles.labelEn}> / City &amp; Area</span>
          </label>
          <input
            id="location"
            type="text"
            className={`${styles.input} ${
              errors.location && touched.location ? styles.inputError : ''
            }`}
            placeholder="e.g. Sadashiv Peth, Pune"
            value={form.location}
            onChange={(e) => handleChange('location', e.target.value)}
            onBlur={() => handleBlur('location')}
            disabled={loading}
            autoComplete="address-level2"
          />
          {errors.location && touched.location && (
            <span className={styles.errorMsg}>{errors.location}</span>
          )}
        </div>

        <div className={styles.field}>
          <label className={styles.label} htmlFor="businessType">
            Dukaan ka prakar
            <span className={styles.labelEn}> / Business Type</span>
          </label>
          <div className={styles.selectWrapper}>
            <select
              id="businessType"
              className={`${styles.select} ${
                errors.businessType && touched.businessType
                  ? styles.inputError : ''
              }`}
              value={form.businessType}
              onChange={(e) => handleChange('businessType', e.target.value)}
              onBlur={() => handleBlur('businessType')}
              disabled={loading}
            >
              <option value="" disabled>Select your business type</option>
              {BUSINESS_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
            <span className={styles.selectChevron} aria-hidden="true">
              ↓
            </span>
          </div>
          {errors.businessType && touched.businessType && (
            <span className={styles.errorMsg}>{errors.businessType}</span>
          )}
        </div>

        {errors.api && (
          <div className={styles.apiError}>
            <span className={styles.apiErrorDot} />
            {errors.api}
          </div>
        )}

        <button
          type="submit"
          className={styles.submitBtn}
          disabled={loading}
        >
          {loading ? (
            <>
              <Loader2 className={styles.spinner} size={18} />
              <span className={styles.btnTextLoading}>
                Creating your application...
              </span>
            </>
          ) : (
            <>
              <span>Continue</span>
              <span className={styles.btnArrow} aria-hidden="true">→</span>
            </>
          )}
        </button>

      </form>

      <p className={styles.trustLine}>
        🔒 Your data is encrypted and protected under{' '}
        <strong>DPDP Act 2023</strong>. We never share it without
        your explicit consent.
      </p>

    </div>
  );
}
