<template>
  <div class="home">

    <!-- Ambient glows -->
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>
    <div class="dots dots-tl"></div>
    <div class="dots dots-br"></div>

    <!-- Navbar -->
    <nav class="navbar">
      <div class="nav-brand">
        <div class="nav-icon">⚡</div>
        <img src="/sellynx-logo.svg" alt="SELLYNX" class="nav-logo" />
      </div>
      <div class="nav-tabs">
        <RouterLink to="/home" class="nav-tab active">Home</RouterLink>
        <RouterLink to="/scoring" class="nav-tab accent">Launch Scoring ↗</RouterLink>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="badge">⚡ AI-Powered · Now Live</div>
      <h1 class="hero-title">
        Qualify Your Clients<br/>
        <span class="gradient-text">Smarter with AI</span>
      </h1>
      <p class="hero-sub">
        Powered by advanced AI models trained on your CRM data,<br/>
        web signals, and LinkedIn — in seconds.
      </p>
      <RouterLink to="/scoring" class="hero-btn">
        Launch Scoring ⚡
      </RouterLink>
      <div class="hero-scroll">
        <div class="scroll-icon"></div>
      </div>
    </section>

    <!-- Challenge section -->
    <section class="challenge">
      <h2 class="section-title">The Qualification Challenge</h2>
      <p class="section-sub">Sales teams face unprecedented complexity qualifying leads at scale</p>

      <div class="compare-grid">
        <!-- Traditional -->
        <div class="compare-col">
          <h3 class="col-title col-bad">Traditional Approach</h3>
          <div class="feat-card bad">
            <span class="feat-icon">⚠️</span>
            <div>
              <div class="feat-name">Manual Research</div>
              <div class="feat-desc">Hours spent googling each prospect individually</div>
            </div>
          </div>
          <div class="feat-card bad">
            <span class="feat-icon">📋</span>
            <div>
              <div class="feat-name">CRM Data Gaps</div>
              <div class="feat-desc">Missing fields, outdated info, no web enrichment</div>
            </div>
          </div>
          <div class="feat-card bad">
            <span class="feat-icon">⏱️</span>
            <div>
              <div class="feat-name">Slow Scoring</div>
              <div class="feat-desc">Days to qualify a batch of accounts manually</div>
            </div>
          </div>
        </div>

        <!-- AI -->
        <div class="compare-col">
          <h3 class="col-title col-good">AI-Powered Solution</h3>
          <div class="feat-card good">
            <span class="feat-icon">🧠</span>
            <div>
              <div class="feat-name">Intelligent Extraction</div>
              <div class="feat-desc">AI reads CRM, website, LinkedIn simultaneously</div>
            </div>
          </div>
          <div class="feat-card good">
            <span class="feat-icon">⚡</span>
            <div>
              <div class="feat-name">Real-Time Enrichment</div>
              <div class="feat-desc">Auto-fills missing data from web & social signals</div>
            </div>
          </div>
          <div class="feat-card good">
            <span class="feat-icon">✅</span>
            <div>
              <div class="feat-name">Instant Qualification</div>
              <div class="feat-desc">Full scoring with justification in under 10 seconds</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features strip -->
    <section class="features">
      <div class="feat-strip-card" v-for="f in features" :key="f.title">
        <div class="strip-icon">{{ f.icon }}</div>
        <div class="strip-title">{{ f.title }}</div>
        <div class="strip-desc">{{ f.desc }}</div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="cta-card">
        <div class="badge badge-sm">⚡ Ready to use</div>
        <h2 class="cta-title">Start Qualifying<br/>Your Clients Now</h2>
        <p class="cta-sub">Enter a Salesforce Account ID and get a full AI-powered qualification report instantly</p>
        <RouterLink to="/scoring" class="hero-btn">
          Start Scoring ⚡
        </RouterLink>
      </div>
    </section>

  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
const features = [
  { icon: '🗄️', title: 'CRM Integration', desc: 'Reads directly from your Elasticsearch / Salesforce data' },
  { icon: '🌐', title: 'Web Crawling', desc: 'Scrapes company website for numbers, keywords, signals' },
  { icon: '💼', title: 'LinkedIn Signals', desc: 'Resolves LinkedIn from CRM, meta tags, or name inference' },
  { icon: '📊', title: 'Criteria Scoring', desc: 'Evaluates numeric, choice & text criteria with evidence' },
  { icon: '🔗', title: 'Evidence Links', desc: 'Every score is backed by a clickable source URL' },
  { icon: '🎯', title: 'Eligibility Status', desc: 'Eligible / To Review / Not Eligible with confidence score' },
]
</script>

<style scoped>
.home { min-height: 100vh; background: #060E1A; color: #fff; position: relative; overflow: hidden; }

/* Ambient glows */
.glow { position: fixed; border-radius: 50%; filter: blur(120px); pointer-events: none; z-index: 0; }
.glow-1 { width: 600px; height: 600px; background: radial-gradient(circle, rgba(232,98,44,0.12) 0%, transparent 70%); top: -200px; left: -200px; }
.glow-2 { width: 500px; height: 500px; background: radial-gradient(circle, rgba(10,45,74,0.6) 0%, transparent 70%); bottom: -100px; right: -100px; }

/* Dot grids */
.dots { position: fixed; pointer-events: none; z-index: 0; opacity: 0.15;
  background-image: radial-gradient(circle, #E8622C 1px, transparent 1px);
  background-size: 28px 28px; }
.dots-tl { width: 280px; height: 280px; top: 40px; left: 40px; }
.dots-br { width: 280px; height: 280px; bottom: 40px; right: 40px; }

/* Navbar */
.navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 48px;
  background: rgba(6,14,26,0.85); backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(232,98,44,0.1); }
.nav-brand { display: flex; align-items: center; gap: 10px; }
.nav-icon { width: 34px; height: 34px; background: linear-gradient(135deg, #E8622C, #ff8c5a);
  border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 16px; }
.nav-logo { height: 28px; }
.nav-tabs { display: flex; gap: 8px; }
.nav-tab { padding: 8px 20px; border-radius: 8px; font-size: 14px; font-weight: 500;
  text-decoration: none; color: rgba(255,255,255,0.6); border: 1px solid transparent;
  transition: all 0.2s; }
.nav-tab:hover { color: #fff; }
.nav-tab.active { color: #fff; border-color: rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); }
.nav-tab.accent { color: #fff; background: #E8622C; border-color: #E8622C; font-weight: 600; }
.nav-tab.accent:hover { background: #cf5224; }

/* Hero */
.hero { position: relative; z-index: 1; min-height: 100vh; display: flex; flex-direction: column;
  align-items: center; justify-content: center; text-align: center; padding: 120px 40px 80px; }
.badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 16px;
  background: rgba(232,98,44,0.15); border: 1px solid rgba(232,98,44,0.3);
  border-radius: 99px; font-size: 13px; color: #E8622C; font-weight: 500; margin-bottom: 32px; }
.badge-sm { font-size: 12px; margin-bottom: 20px; }
.hero-title { font-size: clamp(42px, 6vw, 72px); font-weight: 800; line-height: 1.1;
  letter-spacing: -1px; margin-bottom: 20px; color: #fff; }
.gradient-text { background: linear-gradient(90deg, #E8622C, #ff9a6c, #E8622C);
  background-size: 200%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; animation: shimmer 3s linear infinite; }
@keyframes shimmer { 0% { background-position: 0% } 100% { background-position: 200% } }
.hero-sub { font-size: 17px; color: rgba(255,255,255,0.55); line-height: 1.7;
  max-width: 520px; margin-bottom: 40px; }
.hero-btn { display: inline-flex; align-items: center; gap: 8px; padding: 16px 36px;
  background: linear-gradient(135deg, #E8622C, #ff7a45); color: #fff;
  font-size: 16px; font-weight: 700; border-radius: 12px; text-decoration: none;
  box-shadow: 0 8px 32px rgba(232,98,44,0.35); transition: all 0.2s; }
.hero-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(232,98,44,0.5); }
.hero-scroll { margin-top: 60px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
.scroll-icon { width: 24px; height: 38px; border: 2px solid rgba(255,255,255,0.2);
  border-radius: 12px; position: relative; }
.scroll-icon::after { content: ''; position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
  width: 4px; height: 8px; background: #E8622C; border-radius: 2px;
  animation: scrollDown 1.5s ease-in-out infinite; }
@keyframes scrollDown { 0%,100%{top:6px;opacity:1} 50%{top:18px;opacity:0.3} }

/* Challenge */
.challenge { position: relative; z-index: 1; padding: 100px 80px; }
.section-title { font-size: clamp(28px, 4vw, 42px); font-weight: 800; text-align: center;
  margin-bottom: 12px; background: linear-gradient(90deg, #fff, #E8622C);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.section-sub { text-align: center; color: rgba(255,255,255,0.45); font-size: 15px; margin-bottom: 60px; }
.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; max-width: 1100px; margin: 0 auto; }
.col-title { font-size: 18px; font-weight: 700; margin-bottom: 16px; }
.col-bad { color: rgba(255,255,255,0.5); }
.col-good { color: #E8622C; }
.feat-card { display: flex; align-items: flex-start; gap: 14px; padding: 18px 20px;
  border-radius: 12px; margin-bottom: 12px; border: 1px solid; transition: transform 0.2s; }
.feat-card:hover { transform: translateX(4px); }
.feat-card.bad { background: rgba(255,255,255,0.03); border-color: rgba(255,80,80,0.2); }
.feat-card.good { background: rgba(232,98,44,0.06); border-color: rgba(232,98,44,0.25); }
.feat-icon { font-size: 22px; flex-shrink: 0; margin-top: 2px; }
.feat-name { font-size: 14px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.feat-desc { font-size: 13px; color: rgba(255,255,255,0.45); line-height: 1.5; }

/* Features strip */
.features { position: relative; z-index: 1; padding: 0 80px 80px;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 1100px; margin: 0 auto; }
.feat-strip-card { padding: 28px 24px; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(232,98,44,0.15); border-radius: 14px; transition: all 0.2s; }
.feat-strip-card:hover { background: rgba(232,98,44,0.07); border-color: rgba(232,98,44,0.35);
  transform: translateY(-3px); }
.strip-icon { font-size: 28px; margin-bottom: 12px; }
.strip-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 6px; }
.strip-desc { font-size: 13px; color: rgba(255,255,255,0.45); line-height: 1.5; }

/* CTA */
.cta-section { position: relative; z-index: 1; padding: 40px 80px 100px; }
.cta-card { max-width: 700px; margin: 0 auto; padding: 60px 48px; text-align: center;
  background: linear-gradient(135deg, rgba(232,98,44,0.1), rgba(10,45,74,0.4));
  border: 1px solid rgba(232,98,44,0.25); border-radius: 24px;
  backdrop-filter: blur(20px);
  box-shadow: 0 0 80px rgba(232,98,44,0.08); }
.cta-title { font-size: clamp(28px, 4vw, 40px); font-weight: 800; color: #fff;
  margin: 16px 0 14px; line-height: 1.2; }
.cta-sub { color: rgba(255,255,255,0.5); font-size: 15px; margin-bottom: 32px; line-height: 1.6; }
</style>
