<template>
  <div class="root">

    <!-- ══════════════════════════════════════════════
         GLOBAL FIXED BACKGROUND (persists across all scroll)
    ══════════════════════════════════════════════ -->
    <div class="bg-canvas" aria-hidden="true">
      <div class="bg-solid"></div>
      <div class="bg-noise"></div>

      <!-- Floating glow blobs -->
      <div class="blob blob-a"></div>
      <div class="blob blob-b"></div>
      <div class="blob blob-c"></div>
      <div class="blob blob-d"></div>

      <!-- Animated waves — full viewport height -->
      <div class="global-waves">
        <svg class="gwave gw1" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,450 C180,320 360,580 540,450 C720,320 900,580 1080,450 C1260,320 1380,500 1440,450 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw2" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,600 C240,480 480,700 720,600 C960,500 1200,700 1440,600 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw3" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,720 C200,650 400,790 600,720 C800,650 1000,790 1200,720 C1320,680 1400,750 1440,720 L1440,900 L0,900 Z"/>
        </svg>
        <svg class="gwave gw4" viewBox="0 0 1440 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,300 C300,180 600,420 900,300 C1100,220 1280,380 1440,300 L1440,900 L0,900 Z"/>
        </svg>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════
         HERO SECTION — 100vh login (unchanged)
    ══════════════════════════════════════════════ -->
    <section class="hero-section">

      <!-- Scroll indicator -->
      <button class="scroll-ring" aria-label="Scroll down" @click="scrollToNext">
        <div class="scroll-dot"></div>
      </button>

      <div class="hero-layout">

        <!-- LEFT -->
        <section class="left">
          <div class="brand anim-1">
            <img src="/sellynx-logo.svg" alt="SELLYNX" class="brand-logo" />
            <span class="brand-sep"></span>
            <span class="brand-tag">Qualify Smarter</span>
          </div>

          <div class="hero-badge anim-2">
            <span class="badge-dot"></span>
            AI-Powered Client Qualification
          </div>

          <h1 class="headline anim-3">
            Qualify your<br/>
            clients<br/>
            <span class="headline-accent">smarter with AI</span>
          </h1>

          <p class="subline anim-4">
            {{ displayed }}<span class="cursor" :class="{ blink: done }">|</span>
          </p>

          <div class="features anim-5">
            <div class="feat">
              <div class="feat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M12 6v6l4 2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="8"/>
                </svg>
              </div>
              <div class="feat-text">
                <span class="feat-title">AI-Powered Scoring</span>
                <span class="feat-sub">Identify high-potential clients instantly</span>
              </div>
            </div>
            <div class="feat">
              <div class="feat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M4 17l5-5 3 3 6-8" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 20h16" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="feat-text">
                <span class="feat-title">Smart Insights</span>
                <span class="feat-sub">Data-driven recommendations at scale</span>
              </div>
            </div>
            <div class="feat">
              <div class="feat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div class="feat-text">
                <span class="feat-title">Secure & Reliable</span>
                <span class="feat-sub">Enterprise-grade security built-in</span>
              </div>
            </div>
          </div>

          <div class="chips anim-6">
            <span class="chip">CRM Integration</span>
            <span class="chip">LinkedIn Data</span>
            <span class="chip">Real-time Scoring</span>
            <span class="chip">AI Extraction</span>
          </div>
        </section>

        <!-- RIGHT: login card -->
        <section class="right anim-card">
          <div class="card">
            <div class="card-glow"></div>
            <div class="card-body">
              <p class="card-eyebrow">Welcome back</p>
              <h2 class="card-title">Sign in</h2>
              <p class="card-sub">Enter your credentials to access Sellynx</p>

              <form @submit.prevent="handleLogin" class="login-form">

                <div class="field">
                  <label class="field-label" for="lf-username">Email</label>
                  <input
                    id="lf-username"
                    v-model="username"
                    type="email"
                    class="field-input"
                    placeholder="Enter your email"
                    autocomplete="email"
                    :disabled="loading"
                  />
                </div>

                <div class="field">
                  <label class="field-label" for="lf-password">Password</label>
                  <div class="field-pw-wrap">
                    <input
                      id="lf-password"
                      v-model="password"
                      :type="showPw ? 'text' : 'password'"
                      class="field-input"
                      placeholder="Enter your password"
                      autocomplete="current-password"
                      :disabled="loading"
                    />
                    <button type="button" class="pw-toggle" @click="showPw = !showPw" tabindex="-1" :aria-label="showPw ? 'Hide password' : 'Show password'">
                      <svg v-if="!showPw" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                      </svg>
                      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
                      </svg>
                    </button>
                  </div>
                </div>

                <transition name="err">
                  <div v-if="authError" class="login-error" role="alert">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    {{ authError }}
                  </div>
                </transition>

                <button type="submit" :disabled="loading || !username || !password" class="btn-main">
                  <span v-if="!loading" class="btn-main-inner">
                    Sign in
                    <svg class="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                      <path d="M5 12h14" stroke-linecap="round"/><path d="M13 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                  <span v-else class="spinner"></span>
                </button>

              </form>

              <p class="card-footer">
                No account? <a href="#">Contact your admin</a>
              </p>
            </div>
          </div>
        </section>

      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         SECTION 1 — The Problem
    ══════════════════════════════════════════════ -->
    <section id="section-challenge" class="lp-section s-challenge" ref="secChallenge">
      <div class="s-glow glow-violet"></div>
      <div class="section-inner">

        <div class="section-head observe">
          <span class="section-badge">The Challenge</span>
          <h2 class="section-title">Traditional Qualification<br/><span class="title-dim">is Broken</span></h2>
          <p class="section-sub">Modern sales teams face an overwhelming qualification problem that costs time, money, and deals.</p>
        </div>

        <div class="challenge-grid">
          <div class="challenge-card observe delay-1">
            <div class="cc-icon cc-red">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12" stroke-linecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Manual &amp; Slow</h3>
            <p>Sales reps spend up to 40% of their time manually researching and qualifying leads — time that should go to closing.</p>
            <div class="cc-stat">40% of time wasted</div>
          </div>
          <div class="challenge-card observe delay-2">
            <div class="cc-icon cc-red">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke-linecap="round" stroke-linejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke-linecap="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>High Error Rate</h3>
            <p>Without structured scoring, wrong-fit clients slip through the funnel — burning budget on deals that will never close.</p>
            <div class="cc-stat">3x higher churn risk</div>
          </div>
          <div class="challenge-card observe delay-3">
            <div class="cc-icon cc-red">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>No Prioritization</h3>
            <p>Without data-driven signals, every lead looks the same. Your best opportunities are invisible until it's too late.</p>
            <div class="cc-stat">60% of deals mis-prioritized</div>
          </div>
        </div>

      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         SECTION 2 — The Solution
    ══════════════════════════════════════════════ -->
    <section class="lp-section s-solution">
      <div class="s-glow glow-orange"></div>
      <div class="section-inner">

        <div class="section-head observe">
          <span class="section-badge accent">AI-Powered Solution</span>
          <h2 class="section-title">Meet Intelligent<br/><span class="title-accent">Client Scoring</span></h2>
          <p class="section-sub">Sellynx replaces guesswork with a fully automated AI pipeline that scores, ranks, and explains every lead.</p>
        </div>

        <div class="solution-split">

          <!-- Before -->
          <div class="split-col observe delay-1">
            <h4 class="split-label red">Before Sellynx</h4>
            <div class="split-items">
              <div class="split-item bad">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                <div>
                  <strong>Manual research</strong>
                  <p>Hours spent browsing LinkedIn and company sites</p>
                </div>
              </div>
              <div class="split-item bad">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                <div>
                  <strong>Gut-feel decisions</strong>
                  <p>No consistent scoring framework or criteria</p>
                </div>
              </div>
              <div class="split-item bad">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                <div>
                  <strong>Missed opportunities</strong>
                  <p>High-potential leads lost to slow qualification</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Divider -->
          <div class="split-divider observe delay-2">
            <div class="divider-line"></div>
            <div class="divider-vs">VS</div>
            <div class="divider-line"></div>
          </div>

          <!-- After -->
          <div class="split-col observe delay-3">
            <h4 class="split-label green">With Sellynx</h4>
            <div class="split-items">
              <div class="split-item good">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                <div>
                  <strong>Automated AI pipeline</strong>
                  <p>Crawls web, LinkedIn & CRM — scored in seconds</p>
                </div>
              </div>
              <div class="split-item good">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                <div>
                  <strong>Criteria-based scoring</strong>
                  <p>Consistent, explainable scores across all leads</p>
                </div>
              </div>
              <div class="split-item good">
                <svg class="si-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                <div>
                  <strong>Real-time prioritization</strong>
                  <p>Focus on the leads most likely to convert</p>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         SECTION 3 — Capabilities
    ══════════════════════════════════════════════ -->
    <section class="lp-section s-features">
      <div class="s-glow glow-blue"></div>
      <div class="section-inner">

        <div class="section-head observe">
          <span class="section-badge">Core Capabilities</span>
          <h2 class="section-title">Everything you need to<br/><span class="title-accent">qualify at scale</span></h2>
          <p class="section-sub">A complete intelligence stack — from data collection to actionable scores.</p>
        </div>

        <div class="caps-grid">
          <div class="cap-card observe delay-1">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>CRM Sync</h3>
            <p>Pull structured data directly from Salesforce — employee count, sector, website — no manual entry.</p>
          </div>
          <div class="cap-card observe delay-2">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Web Intelligence</h3>
            <p>Automatically crawls company websites and LinkedIn profiles to extract evidence for every criterion.</p>
          </div>
          <div class="cap-card observe delay-3">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Semantic Scoring</h3>
            <p>Embeddings + LLM extraction identify relevant evidence and map it to scoring criteria automatically.</p>
          </div>
          <div class="cap-card observe delay-1">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Explainable Results</h3>
            <p>Every score comes with evidence — exact quotes, source URLs, and reasoning for full transparency.</p>
          </div>
          <div class="cap-card observe delay-2">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9" stroke-linecap="round"/>
              </svg>
            </div>
            <h3>Product Rules</h3>
            <p>Configure scoring criteria per product. Blocking rules, weighted scores, and conditional branching.</p>
          </div>
          <div class="cap-card observe delay-3">
            <div class="cap-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
                <path d="M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <h3>Enterprise Ready</h3>
            <p>Keycloak SSO, role-based access, audit logs — built for teams that take security seriously.</p>
          </div>
        </div>

        <!-- Data chips -->
        <div class="data-chips observe">
          <span class="dchip">Salesforce</span>
          <span class="dchip">LinkedIn</span>
          <span class="dchip">Wikipedia</span>
          <span class="dchip">Company Websites</span>
          <span class="dchip">OpenAI GPT-4o</span>
          <span class="dchip">Vector Embeddings</span>
          <span class="dchip">Keycloak SSO</span>
        </div>

      </div>
    </section>

    <!-- ══════════════════════════════════════════════
         SECTION 4 — CTA
    ══════════════════════════════════════════════ -->
    <section class="lp-section s-cta">

      <div class="s-glow glow-cta"></div>

      <div class="section-inner cta-inner observe">
        <div class="cta-box">
          <div class="cta-glow-ring"></div>
          <span class="cta-badge">
            <span class="badge-dot"></span>
            Ready to get started
          </span>
          <h2 class="cta-title">
            Start Qualifying<br/>
            <span class="title-accent">Smarter Today</span>
          </h2>
          <p class="cta-sub">
            Join your team on Sellynx and transform how you identify<br/>
            and prioritize your highest-value clients.
          </p>
          <div class="cta-actions">
            <button @click="handleLogin" :disabled="loading" class="btn-main cta-btn">
              <span class="btn-main-inner">
                Sign in with SELLYNX
                <svg class="btn-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <path d="M5 12h14" stroke-linecap="round"/><path d="M13 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </button>
            <button class="btn-ghost" @click="scrollToTop">Back to top ↑</button>
          </div>
          <div class="cta-stats">
            <div class="stat"><span class="stat-num">2 min</span><span class="stat-label">Average scoring time</span></div>
            <div class="stat-sep"></div>
            <div class="stat"><span class="stat-num">100%</span><span class="stat-label">Explainable AI results</span></div>
            <div class="stat-sep"></div>
            <div class="stat"><span class="stat-num">5+</span><span class="stat-label">Data sources per client</span></div>
          </div>
        </div>
      </div>

    </section>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../auth/useAuth'

const router = useRouter()
const { login } = useAuth()

const loading  = ref(false)
const username = ref('')
const password = ref('')
const showPw   = ref(false)
const authError = ref('')

// ── Typing animation ──
const fullText  = 'The intelligent platform to identify high-potential clients and close more deals.'
const displayed = ref('')
const done      = ref(false)

onMounted(() => {
  let i = 0
  const tick = setInterval(() => {
    if (i <= fullText.length) { displayed.value = fullText.slice(0, i++) }
    else { done.value = true; clearInterval(tick) }
  }, 28)

  // Intersection Observer for scroll-triggered animations
  const io = new IntersectionObserver(
    entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('in-view') }),
    { threshold: 0.12 }
  )
  document.querySelectorAll('.observe').forEach(el => io.observe(el))
})

// ── Scroll helpers ──
const secChallenge = ref(null)
function scrollToNext() { secChallenge.value?.scrollIntoView({ behavior: 'smooth' }) }
function scrollToTop()  { window.scrollTo({ top: 0, behavior: 'smooth' }) }

// ── Auth ──
async function handleLogin() {
  authError.value = ''
  loading.value   = true
  try {
    await login(username.value.trim(), password.value)
    router.push('/search')
  } catch (e) {
    authError.value = e.message || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ══════════════════════════════════════════
   GLOBAL RESET & ROOT
══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.root {
  background: #060E1A;
  font-family: 'Inter', 'Plus Jakarta Sans', system-ui, sans-serif;
  color: #fff;
}

/* ══════════════════════════════════════════
   GLOBAL FIXED BACKGROUND CANVAS
══════════════════════════════════════════ */
.bg-canvas {
  position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden;
}

.bg-solid { position: absolute; inset: 0; background: #060E1A; }

.bg-noise {
  position: absolute; inset: 0; opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 200px;
}

/* Floating glow blobs — fixed, drift slowly */
.blob { position: absolute; border-radius: 50%; pointer-events: none; filter: blur(110px); }
.blob-a {
  width: 780px; height: 780px;
  background: radial-gradient(circle, rgba(59,91,219,0.26) 0%, transparent 70%);
  bottom: 5%; left: -10%;
  animation: float1 13s ease-in-out infinite alternate;
}
.blob-b {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(124,58,237,0.20) 0%, transparent 70%);
  top: 20%; left: 20%;
  animation: float2 17s ease-in-out infinite alternate;
}
.blob-c {
  width: 420px; height: 420px;
  background: radial-gradient(circle, rgba(232,98,44,0.18) 0%, transparent 70%);
  top: 10%; right: 5%;
  animation: float3 11s ease-in-out infinite alternate;
}
.blob-d {
  width: 500px; height: 500px;
  background: radial-gradient(circle, rgba(59,130,246,0.14) 0%, transparent 70%);
  bottom: 20%; right: -5%;
  animation: float1 15s ease-in-out infinite alternate-reverse;
}
@keyframes float1 { to { transform: translate(60px,-50px) scale(1.08); } }
@keyframes float2 { to { transform: translate(-50px,40px) scale(0.92); } }
@keyframes float3 { to { transform: translate(40px,-60px) scale(1.18); } }

/* Global animated waves */
.global-waves {
  position: absolute; inset: 0;
}
.gwave {
  position: absolute; left: 0; width: 100%; height: 100%;
}
.gw1 {
  fill: rgba(59,91,219,0.09);
  animation: waveFlow1 5s ease-in-out infinite alternate;
  transform-origin: center bottom;
}
.gw2 {
  fill: rgba(124,58,237,0.075);
  animation: waveFlow2 7s ease-in-out infinite alternate-reverse;
  transform-origin: center bottom;
}
.gw3 {
  fill: rgba(232,98,44,0.06);
  animation: waveFlow3 4s ease-in-out infinite alternate;
  transform-origin: center bottom;
}
.gw4 {
  fill: rgba(59,130,246,0.05);
  animation: waveFlow4 9s ease-in-out infinite alternate-reverse;
  transform-origin: center bottom;
}

@keyframes waveFlow1 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  25%  { transform: translateX(-5%)  scaleY(1.08) scaleX(1.04); }
  75%  { transform: translateX(4%)   scaleY(0.93) scaleX(0.97); }
  100% { transform: translateX(-7%)  scaleY(1.11) scaleX(1.05); }
}
@keyframes waveFlow2 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  30%  { transform: translateX(7%)   scaleY(1.09) scaleX(1.05); }
  65%  { transform: translateX(-4%)  scaleY(0.92) scaleX(0.96); }
  100% { transform: translateX(6%)   scaleY(1.12) scaleX(1.06); }
}
@keyframes waveFlow3 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  40%  { transform: translateX(-6%)  scaleY(1.13) scaleX(1.06); }
  100% { transform: translateX(5%)   scaleY(0.90) scaleX(0.95); }
}
@keyframes waveFlow4 {
  0%   { transform: translateX(0%)   scaleY(1)    scaleX(1); }
  20%  { transform: translateX(8%)   scaleY(1.07) scaleX(1.04); }
  55%  { transform: translateX(-5%)  scaleY(0.94) scaleX(1.03); }
  100% { transform: translateX(7%)   scaleY(1.10) scaleX(0.96); }
}

/* ══════════════════════════════════════════
   HERO SECTION
══════════════════════════════════════════ */
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex; align-items: center;
  z-index: 1;
}

/* Scroll indicator */
.scroll-ring {
  position: absolute; bottom: 28px; left: 50%; transform: translateX(-50%);
  width: 26px; height: 44px;
  border: 2px solid rgba(255,255,255,0.18);
  border-radius: 13px;
  background: none; cursor: pointer;
  display: flex; justify-content: center; padding-top: 8px;
  animation: fadeIn 1s 1.8s both;
  z-index: 4;
  transition: border-color 0.2s;
}
.scroll-ring:hover { border-color: rgba(232,98,44,0.55); }
.scroll-dot {
  width: 4px; height: 8px; background: rgba(255,255,255,0.35); border-radius: 2px;
  animation: scrollBounce 2.2s ease-in-out infinite;
}
@keyframes scrollBounce { 0%,100% { transform:translateY(0); opacity:1; } 60% { transform:translateY(8px); opacity:0.3; } }

/* Hero layout */
.hero-layout {
  position: relative; z-index: 2;
  width: 100%; max-width: 1160px; margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 64px;
  align-items: center;
  padding: 64px 48px 100px;
  min-height: 100vh;
}

/* Entrance animations */
@keyframes riseIn { from { opacity:0; transform:translateY(28px); } to { opacity:1; transform:translateY(0); } }
@keyframes fadeIn  { from { opacity:0; } to { opacity:1; } }

.anim-1    { animation: riseIn 0.7s cubic-bezier(.22,1,.36,1) 0.05s both; }
.anim-2    { animation: riseIn 0.7s cubic-bezier(.22,1,.36,1) 0.15s both; }
.anim-3    { animation: riseIn 0.8s cubic-bezier(.22,1,.36,1) 0.22s both; }
.anim-4    { animation: riseIn 0.7s cubic-bezier(.22,1,.36,1) 0.32s both; }
.anim-5    { animation: riseIn 0.7s cubic-bezier(.22,1,.36,1) 0.40s both; }
.anim-6    { animation: riseIn 0.7s cubic-bezier(.22,1,.36,1) 0.50s both; }
.anim-card { animation: riseIn 0.85s cubic-bezier(.22,1,.36,1) 0.10s both; }

/* Brand */
.left { display: flex; flex-direction: column; gap: 36px; }
.brand { display: flex; align-items: center; gap: 14px; }
.brand-logo { height: 30px; }
.brand-sep { width: 1px; height: 20px; background: rgba(255,255,255,0.15); }
.brand-tag { font-size: 10px; letter-spacing: 0.3em; text-transform: uppercase; color: rgba(255,255,255,0.28); }

/* Badge */
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 99px;
  background: linear-gradient(135deg, rgba(232,98,44,0.12), rgba(124,58,237,0.08));
  border: 1px solid rgba(232,98,44,0.25);
  font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.65);
  width: fit-content;
}
.badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #E8622C; box-shadow: 0 0 6px #E8622C;
  animation: pulse 2.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.5; transform:scale(0.7); } }

/* Headline */
.headline {
  font-size: clamp(40px,5.5vw,62px); font-weight: 800;
  line-height: 1.06; letter-spacing: -0.025em; color: #fff;
}
.headline-accent {
  background: linear-gradient(90deg, #E8622C 0%, #ff9a6c 60%, #E8622C 100%);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 4s linear infinite;
}
@keyframes shimmer { to { background-position: 200% center; } }

/* Typing */
.subline { font-size: 15px; line-height: 1.75; color: rgba(255,255,255,0.42); max-width: 420px; min-height: 52px; }
.cursor { display: inline-block; color: #E8622C; animation: caretBlink 0.9s step-end infinite; }
.cursor.blink { animation: caretBlink 1.1s step-end infinite; }
@keyframes caretBlink { 0%,100% { opacity:1; } 50% { opacity:0; } }

/* Features */
.features { display: flex; flex-direction: column; gap: 14px; }
.feat {
  position: relative; overflow: hidden;
  display: flex; align-items: center; gap: 14px; padding: 14px 16px;
  border-radius: 14px; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  transition: background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s cubic-bezier(0.34,1.3,0.64,1);
}
.feat::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.055) 50%, transparent 70%);
  transform: translateX(-130%);
  transition: transform 0.55s cubic-bezier(.22,1,.36,1);
  pointer-events: none; z-index: 1;
}
.feat:hover { background: rgba(255,255,255,0.05); border-color: rgba(232,98,44,0.22); box-shadow: 0 4px 20px rgba(232,98,44,0.07), 0 0 0 1px rgba(232,98,44,0.10); transform: translateX(4px); }
.feat:hover::before { transform: translateX(130%); }
.feat-icon {
  width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px;
  background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.2);
  display: flex; align-items: center; justify-content: center; color: #E8622C;
}
.feat-icon svg { width: 18px; height: 18px; }
.feat-text { display: flex; flex-direction: column; gap: 2px; }
.feat-title { font-size: 13.5px; font-weight: 600; color: #fff; }
.feat-sub   { font-size: 12px; color: rgba(255,255,255,0.35); }

/* Chips */
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
  padding: 5px 14px; border-radius: 99px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10);
  font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.45); transition: all 0.18s;
}
.chip:hover { background: rgba(232,98,44,0.08); border-color: rgba(232,98,44,0.28); color: rgba(255,255,255,0.75); }

/* Login card */
.right { display: flex; align-items: center; justify-content: center; }
.card {
  position: relative; width: 100%; border-radius: 28px;
  background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.09);
  backdrop-filter: blur(32px);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.04) inset, 0 32px 80px rgba(0,0,0,0.55), 0 8px 24px rgba(0,0,0,0.3);
  overflow: hidden;
  transition: transform 0.45s cubic-bezier(0.34,1.3,0.64,1), box-shadow 0.45s ease, border-color 0.45s ease;
}
.card::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.09) 50%, transparent 70%);
  transform: translateX(-150%);
  transition: transform 0.8s cubic-bezier(.22,1,.36,1);
  pointer-events: none; z-index: 1;
}
.card:hover { transform: translateY(-6px) scale(1.008); border-color: rgba(232,98,44,0.28); box-shadow: 0 0 0 1px rgba(232,98,44,0.15) inset, 0 40px 100px rgba(0,0,0,0.6), 0 0 0 1px rgba(232,98,44,0.12), 0 0 60px rgba(232,98,44,0.12), 0 0 100px rgba(59,91,219,0.08); }
.card:hover::before { transform: translateX(150%); }
.card-glow {
  position: absolute; top: -80px; left: 50%; transform: translateX(-50%);
  width: 300px; height: 200px;
  background: radial-gradient(ellipse, rgba(232,98,44,0.18) 0%, transparent 70%); pointer-events: none;
}
.card-body { padding: 44px 40px; }
.card-eyebrow { font-size: 12.5px; font-weight: 600; color: #E8622C; margin-bottom: 6px; }
.card-title   { font-size: 32px; font-weight: 800; color: #fff; letter-spacing: -0.025em; line-height: 1.1; }
.card-sub     { font-size: 14px; color: rgba(255,255,255,0.35); margin-top: 6px; margin-bottom: 32px; }

/* Primary button */
.btn-main {
  position: relative; width: 100%; height: 52px; border-radius: 14px; border: none; cursor: pointer;
  background: linear-gradient(135deg, #E8622C 0%, #ff8244 50%, #E8622C 100%);
  background-size: 200% auto; color: #fff; font-size: 14.5px; font-weight: 700;
  box-shadow: 0 4px 28px rgba(232,98,44,0.38), 0 1px 0 rgba(255,255,255,0.15) inset;
  transition: transform 0.18s, box-shadow 0.18s, background-position 0.4s; overflow: hidden;
}
.btn-main::after { content: ''; position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(255,255,255,0.12) 0%, transparent 60%); pointer-events: none; }
.btn-main:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 36px rgba(232,98,44,0.5), 0 1px 0 rgba(255,255,255,0.15) inset; background-position: right center; }
.btn-main:active:not(:disabled) { transform: translateY(0); }
.btn-main:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-main-inner { display: flex; align-items: center; justify-content: center; gap: 8px; position: relative; z-index: 1; }
.btn-arrow { width: 16px; height: 16px; transition: transform 0.18s; }
.btn-main:hover .btn-arrow { transform: translateX(3px); }

.spinner { display: block; margin: 0 auto; width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.25); border-top-color: #fff; border-radius: 50%; animation: spin 0.65s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }



.card-footer { margin-top: 24px; text-align: center; font-size: 12.5px; color: rgba(255,255,255,0.28); }
.card-footer a { color: #E8622C; font-weight: 600; text-decoration: none; margin-left: 4px; transition: color 0.15s; }
.card-footer a:hover { color: #ff8a5c; }

/* ── Login form ── */
.login-form { display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 7px; }
.field-label { font-size: 12.5px; font-weight: 600; color: rgba(255,255,255,0.55); letter-spacing: 0.02em; }
.field-input {
  width: 100%; height: 46px; padding: 0 14px;
  border-radius: 12px; border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.04);
  color: #fff; font-size: 14px; font-family: inherit;
  outline: none; transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}
.field-input::placeholder { color: rgba(255,255,255,0.22); }
.field-input:focus { border-color: rgba(232,98,44,0.5); background: rgba(255,255,255,0.06); box-shadow: 0 0 0 3px rgba(232,98,44,0.12); }
.field-input:disabled { opacity: 0.5; cursor: not-allowed; }

.field-pw-wrap { position: relative; }
.field-pw-wrap .field-input { padding-right: 44px; }
.pw-toggle {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; padding: 4px;
  color: rgba(255,255,255,0.3); transition: color 0.18s;
  display: flex; align-items: center;
}
.pw-toggle:hover { color: rgba(255,255,255,0.7); }
.pw-toggle svg { width: 16px; height: 16px; }

.login-error {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; border-radius: 10px;
  background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
  color: #f87171; font-size: 13px; line-height: 1.4;
}
.login-error svg { width: 16px; height: 16px; flex-shrink: 0; }

/* Error transition */
.err-enter-active { transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.34,1.3,0.64,1); }
.err-leave-active { transition: opacity 0.2s ease; }
.err-enter-from  { opacity: 0; transform: translateY(-6px); }
.err-leave-to    { opacity: 0; }

/* ══════════════════════════════════════════
   SCROLL-TRIGGERED ANIMATIONS
══════════════════════════════════════════ */
.observe {
  opacity: 0;
  transform: translateY(40px);
  /* cubic-bezier(0.34,1.56,0.64,1) = spring — Y>1 produces the overshoot */
  transition: opacity 0.72s cubic-bezier(.22,1,.36,1),
              transform 0.72s cubic-bezier(0.34,1.56,0.64,1);
}
.observe.in-view { opacity: 1; transform: translateY(0); }
.delay-1 { transition-delay: 0.10s; }
.delay-2 { transition-delay: 0.22s; }
.delay-3 { transition-delay: 0.34s; }

/* ══════════════════════════════════════════
   LANDING SECTIONS — SHARED
══════════════════════════════════════════ */
.lp-section {
  position: relative;
  padding: 120px 48px;
  overflow: hidden;
  z-index: 1;
}
.section-inner {
  position: relative; z-index: 2;
  max-width: 1100px; margin: 0 auto;
}

/* Section glow accents */
.s-glow {
  position: absolute; border-radius: 50%; pointer-events: none; filter: blur(120px); opacity: 0.55;
}
.glow-violet { width: 700px; height: 500px; background: radial-gradient(ellipse, rgba(124,58,237,0.25) 0%, transparent 70%); top: -100px; right: -100px; }
.glow-orange { width: 600px; height: 400px; background: radial-gradient(ellipse, rgba(232,98,44,0.20) 0%, transparent 70%); top: 50%; left: -80px; transform: translateY(-50%); }
.glow-blue   { width: 700px; height: 500px; background: radial-gradient(ellipse, rgba(59,91,219,0.22) 0%, transparent 70%); bottom: -80px; right: 0; }
.glow-cta    { width: 800px; height: 600px; background: radial-gradient(ellipse, rgba(232,98,44,0.18) 0%, transparent 60%); top: 50%; left: 50%; transform: translate(-50%,-50%); }

/* Section header */
.section-head { text-align: center; margin-bottom: 72px; }
.section-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 16px; border-radius: 99px; font-size: 12px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); color: rgba(255,255,255,0.55);
  margin-bottom: 20px;
}
.section-badge.accent { background: rgba(232,98,44,0.1); border-color: rgba(232,98,44,0.3); color: #E8622C; }
.section-title { font-size: clamp(32px,4vw,52px); font-weight: 800; line-height: 1.12; letter-spacing: -0.02em; color: #fff; margin-bottom: 16px; }
.title-dim    { color: rgba(255,255,255,0.35); }
.title-accent {
  background: linear-gradient(90deg, #E8622C, #ff9a6c, #E8622C);
  background-size: 200% auto;
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  animation: shimmer 4s linear infinite;
}
.section-sub { font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.42); max-width: 560px; margin: 0 auto; }

/* Sections are transparent — bg-canvas shows through */
.s-challenge, .s-solution, .s-features, .s-cta { background: transparent; }

/* ══════════════════════════════════════════
   SECTION 1 — CHALLENGE CARDS
══════════════════════════════════════════ */
.challenge-grid {
  display: grid; grid-template-columns: repeat(3,1fr); gap: 24px;
}
.challenge-card {
  position: relative; overflow: hidden;
  padding: 32px 28px; border-radius: 20px;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.07);
  transition: transform 0.35s cubic-bezier(0.34,1.3,0.64,1),
              border-color 0.35s ease,
              box-shadow 0.35s ease;
}
.challenge-card::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 35%, rgba(255,255,255,0.07) 50%, transparent 65%);
  transform: translateX(-130%);
  transition: transform 0.65s cubic-bezier(.22,1,.36,1);
  pointer-events: none; z-index: 1;
}
.challenge-card:hover { transform: translateY(-7px) scale(1.015); border-color: rgba(232,98,44,0.32); box-shadow: 0 20px 60px rgba(0,0,0,0.35), 0 0 0 1px rgba(232,98,44,0.18), 0 0 40px rgba(232,98,44,0.10), 0 0 80px rgba(59,91,219,0.06); }
.challenge-card:hover::before { transform: translateX(130%); }
.cc-icon {
  width: 52px; height: 52px; border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 20px;
}
.cc-red { background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #f87171; }
.cc-icon svg { width: 22px; height: 22px; }
.challenge-card h3 { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 10px; }
.challenge-card p  { font-size: 14px; line-height: 1.65; color: rgba(255,255,255,0.45); margin-bottom: 20px; }
.cc-stat {
  display: inline-block; padding: 4px 12px; border-radius: 99px;
  background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2);
  font-size: 12px; font-weight: 600; color: #f87171;
}

/* ══════════════════════════════════════════
   SECTION 2 — SOLUTION SPLIT
══════════════════════════════════════════ */
.solution-split {
  display: grid; grid-template-columns: 1fr auto 1fr; gap: 48px; align-items: start;
}
.split-label { font-size: 13px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 24px; }
.split-label.red   { color: #f87171; }
.split-label.green { color: #4ade80; }
.split-items { display: flex; flex-direction: column; gap: 16px; }
.split-item {
  position: relative; overflow: hidden;
  display: flex; gap: 14px; align-items: flex-start;
  padding: 18px 20px; border-radius: 16px;
  transition: transform 0.32s cubic-bezier(0.34,1.3,0.64,1),
              border-color 0.3s ease, box-shadow 0.3s ease;
}
.split-item::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 30%, rgba(255,255,255,0.05) 50%, transparent 70%);
  transform: translateX(-130%);
  transition: transform 0.55s cubic-bezier(.22,1,.36,1);
  pointer-events: none;
}
.split-item:hover { transform: translateX(6px); }
.split-item.bad:hover  { border-color: rgba(239,68,68,0.3);  box-shadow: 0 4px 20px rgba(239,68,68,0.08); }
.split-item.good:hover { border-color: rgba(74,222,128,0.3); box-shadow: 0 4px 20px rgba(74,222,128,0.08); }
.split-item:hover::before { transform: translateX(130%); }
.split-item.bad  { background: rgba(239,68,68,0.04); border: 1px solid rgba(239,68,68,0.15); }
.split-item.good { background: rgba(74,222,128,0.04); border: 1px solid rgba(74,222,128,0.15); }
.si-icon { width: 20px; height: 20px; flex-shrink: 0; margin-top: 2px; }
.split-item.bad  .si-icon { color: #f87171; }
.split-item.good .si-icon { color: #4ade80; }
.split-item strong { display: block; font-size: 14px; font-weight: 600; color: #fff; margin-bottom: 4px; }
.split-item p { font-size: 13px; color: rgba(255,255,255,0.42); line-height: 1.5; }

.split-divider { display: flex; flex-direction: column; align-items: center; gap: 12px; padding-top: 48px; }
.divider-line  { flex: 1; width: 1px; background: rgba(255,255,255,0.08); }
.divider-vs    { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: rgba(255,255,255,0.2); padding: 8px 12px; border: 1px solid rgba(255,255,255,0.08); border-radius: 99px; }

/* ══════════════════════════════════════════
   SECTION 3 — CAPABILITIES GRID
══════════════════════════════════════════ */
.caps-grid {
  display: grid; grid-template-columns: repeat(3,1fr); gap: 20px; margin-bottom: 48px;
}
.cap-card {
  position: relative; overflow: hidden;
  padding: 28px 24px; border-radius: 18px;
  background: rgba(255,255,255,0.025); border: 1px solid rgba(255,255,255,0.07);
  transition: transform 0.35s cubic-bezier(0.34,1.3,0.64,1),
              border-color 0.35s ease,
              box-shadow 0.35s ease,
              background 0.35s ease;
  cursor: default;
}
.cap-card::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(110deg, transparent 35%, rgba(255,255,255,0.065) 50%, transparent 65%);
  transform: translateX(-130%);
  transition: transform 0.65s cubic-bezier(.22,1,.36,1);
  pointer-events: none; z-index: 1;
}
.cap-card:hover { transform: translateY(-6px) scale(1.015); border-color: rgba(232,98,44,0.28); background: rgba(232,98,44,0.025); box-shadow: 0 16px 48px rgba(0,0,0,0.3), 0 0 0 1px rgba(232,98,44,0.15), 0 0 32px rgba(232,98,44,0.08), 0 0 60px rgba(59,91,219,0.05); }
.cap-card:hover::before { transform: translateX(130%); }
.cap-icon {
  width: 48px; height: 48px; border-radius: 12px; margin-bottom: 18px;
  background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.2);
  display: flex; align-items: center; justify-content: center; color: #E8622C;
}
.cap-icon svg { width: 20px; height: 20px; }
.cap-card h3 { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 8px; }
.cap-card p  { font-size: 13px; line-height: 1.6; color: rgba(255,255,255,0.42); }

/* Data chips */
.data-chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.dchip {
  padding: 6px 16px; border-radius: 99px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10);
  font-size: 12.5px; font-weight: 500; color: rgba(255,255,255,0.45);
  transition: all 0.18s;
}
.dchip:hover { background: rgba(232,98,44,0.08); border-color: rgba(232,98,44,0.28); color: rgba(255,255,255,0.75); }

/* ══════════════════════════════════════════
   SECTION 4 — CTA
══════════════════════════════════════════ */
.cta-inner { text-align: center; }
.cta-box {
  position: relative; display: inline-flex; flex-direction: column; align-items: center;
  max-width: 700px; width: 100%; padding: 72px 60px;
  border-radius: 32px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.09);
  backdrop-filter: blur(24px);
  box-shadow: 0 40px 100px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.06);
  overflow: hidden;
  transition: border-color 0.45s ease, box-shadow 0.45s ease, transform 0.45s cubic-bezier(0.34,1.2,0.64,1);
}
.cta-box::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.055) 50%, transparent 70%);
  transform: translateX(-150%);
  transition: transform 0.9s cubic-bezier(.22,1,.36,1);
  pointer-events: none; z-index: 1;
}
.cta-box:hover { border-color: rgba(232,98,44,0.22); box-shadow: 0 40px 100px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.08), 0 0 0 1px rgba(232,98,44,0.12), 0 0 80px rgba(232,98,44,0.08); transform: translateY(-4px); }
.cta-box:hover::before { transform: translateX(150%); }
.cta-glow-ring {
  position: absolute; top: -120px; left: 50%; transform: translateX(-50%);
  width: 500px; height: 300px;
  background: radial-gradient(ellipse, rgba(232,98,44,0.22) 0%, transparent 70%);
  pointer-events: none;
}
.cta-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 5px 14px; border-radius: 99px; margin-bottom: 28px;
  background: rgba(232,98,44,0.1); border: 1px solid rgba(232,98,44,0.25);
  font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.6);
}
.cta-title { font-size: clamp(36px,4.5vw,56px); font-weight: 800; line-height: 1.1; letter-spacing: -0.025em; color: #fff; margin-bottom: 20px; }
.cta-sub   { font-size: 16px; line-height: 1.7; color: rgba(255,255,255,0.4); margin-bottom: 40px; }
.cta-actions { display: flex; align-items: center; gap: 16px; justify-content: center; margin-bottom: 48px; }
.cta-btn { width: 260px; }

.btn-ghost {
  height: 52px; padding: 0 28px; border-radius: 14px; cursor: pointer;
  background: none; border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.45); font-size: 14px; font-weight: 500;
  transition: all 0.18s;
}
.btn-ghost:hover { border-color: rgba(255,255,255,0.25); color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.05); }

.cta-stats { display: flex; align-items: center; gap: 32px; }
.stat { display: flex; flex-direction: column; gap: 4px; }
.stat-num   { font-size: 24px; font-weight: 800; color: #E8622C; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.35); }
.stat-sep   { width: 1px; height: 40px; background: rgba(255,255,255,0.08); }


/* ══════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════ */
@media (max-width: 960px) {
  .hero-layout { grid-template-columns: 1fr; padding: 48px 24px 80px; gap: 44px; }
  .chips { display: none; }
  .card-body { padding: 32px 28px; }
  .challenge-grid { grid-template-columns: 1fr; }
  .caps-grid { grid-template-columns: 1fr 1fr; }
  .solution-split { grid-template-columns: 1fr; }
  .split-divider { flex-direction: row; padding-top: 0; height: 40px; }
  .divider-line { flex: 1; width: auto; height: 1px; }
  .lp-section { padding: 80px 24px; }
  .cta-box { padding: 48px 28px; }
  .cta-actions { flex-direction: column; }
  .cta-btn { width: 100%; }
  .cta-stats { flex-direction: column; gap: 16px; }
  .stat-sep { width: 40px; height: 1px; }
}
@media (max-width: 600px) {
  .caps-grid { grid-template-columns: 1fr; }
}
</style>
