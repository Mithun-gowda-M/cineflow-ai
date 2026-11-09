# PHASE 1 PLAN: Premium Frontend Design System & Workspaces

> **Phase:** 01 — Premium Frontend  
> **Status:** READY FOR EXECUTION  
> **Goal:** Build the complete, international-grade Next.js 15 frontend with a dark cinematic design system, landing page, student dashboard, media ingestion hub, and professional multi-track video editor.

---

## 🎯 Phase Objectives

1. Create a distinctive, premium dark cinematic visual identity (midnight `#0B0D13`, obsidian `#11141E`, champagne-gold `#E5B869`, electric cyan `#38BDF8`).
2. Implement 6 comprehensive workspaces:
   - **Landing Page (`/`):** High-impact hero, interactive workflow simulation, feature walkthrough, institutional credentials.
   - **Student Dashboard (`/dashboard`):** Project creation, storage quota gauge, recent projects list with live previews.
   - **Upload & Quality Hub (`/upload`):** Batch dropzone (20-30+ files), metadata probing, quality score badges.
   - **Multi-Track Video Editor (`/editor`):** Canvas preview, real-time scrubbing, color grading simulation, multi-track timeline (V1, V2, A1, A2, T1), and AI Director drawer.
   - **Campus Admin Dashboard (`/admin`):** System resource diagnostics, queue monitor, storage allocation.
   - **Student Authentication (`/auth/login`, `/auth/register`):** BMSIT college email validation and role-based views.
3. Guarantee that every interactive control (scrubbing, playback, clip trimming, color grading, aspect ratio switching, undo/redo) performs actual functional state transitions.

---

## 📋 Task Breakdown

### Task 1.1: Frontend Core Setup & Cinematic Design Tokens
- **Target Files:**
  - `apps/web/package.json`
  - `apps/web/tailwind.config.ts`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/components/ui/` (GlassPanel, GoldButton, Badge, Slider, Tooltip)
- **Description:** Define Tailwind color tokens (`cine-black`, `cine-surface`, `cine-card`, `gold-400`, `gold-500`, `cyan-400`). Configure backdrop-blur glassmorphism effects and custom scrollbars.

### Task 1.2: Flagship Cinematic Landing Page (`/`)
- **Target Files:**
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/components/landing/HeroSection.tsx`
  - `apps/web/src/components/landing/InteractiveWorkflowDemo.tsx`
  - `apps/web/src/components/landing/TechStackShowcase.tsx`
  - `apps/web/src/components/landing/InstitutionalBanner.tsx`
- **Description:** Build the landing page with headline *"Your Footage Deserves a Director"*, interactive video editing simulation showcasing beat snapping and color grading, open-source technology badges, and a direct CTA to launch the studio.

### Task 1.3: Student Project Dashboard (`/dashboard`)
- **Target Files:**
  - `apps/web/src/app/dashboard/page.tsx`
  - `apps/web/src/components/dashboard/ProjectCard.tsx`
  - `apps/web/src/components/dashboard/StorageQuotaGauge.tsx`
  - `apps/web/src/components/dashboard/NewProjectModal.tsx`
- **Description:** Build the dashboard displaying user projects (Deepavali 2026 Recap, BMSIT Tech Fest, Goa Travel Montage), storage quota usage (`4.8 GB / 25 GB`), and modal to initiate a new project with aspect ratio and duration targets.

### Task 1.4: Media Ingestion & Quality Analysis Hub (`/upload`)
- **Target Files:**
  - `apps/web/src/app/upload/page.tsx`
  - `apps/web/src/components/upload/BatchDropzone.tsx`
  - `apps/web/src/components/upload/MediaInspectionCard.tsx`
- **Description:** Multi-file uploader supporting 20-30+ files with simulated metadata extraction (resolution, duration, fps, codec), OpenCV blur/sharpness score (0-100), and auto-tags (Diya, Fireworks, Action, Sunset).

### Task 1.5: Professional Multi-Track Video Editor (`/editor`)
- **Target Files:**
  - `apps/web/src/app/editor/page.tsx`
  - `apps/web/src/components/editor/EditorHeader.tsx` (Aspect ratio selector, Timecode, Undo/Redo, Export button)
  - `apps/web/src/components/editor/MediaLibraryDrawer.tsx` (Clips, Scenes, B-Roll, Sound FX)
  - `apps/web/src/components/editor/VideoPreviewCanvas.tsx` (Scrubbable video canvas, aspect ratio frame masking, play/pause, timecode)
  - `apps/web/src/components/editor/AiDirectorDrawer.tsx` (Natural language prompt box, voice command mic button, style presets, clip trim/speed inspector)
  - `apps/web/src/components/editor/MultiTrackTimeline.tsx` (V1 Main, V2 Overlay, A1 Dialogue, A2 Music/Beats, T1 Subtitles with draggable playhead)
  - `apps/web/src/components/editor/ExportModal.tsx` (Resolution 720p/1080p/4K, MP4 export progress pipeline)
- **Description:** Assemble the complete multi-track video editing studio. Wire state so scrubbing the timeline updates the preview canvas, changing color grade updates canvas CSS filters, and AI commands update the timeline clips.

### Task 1.6: Student Authentication & Campus Admin Dashboard (`/auth/login`, `/admin`)
- **Target Files:**
  - `apps/web/src/app/auth/login/page.tsx`
  - `apps/web/src/app/auth/register/page.tsx`
  - `apps/web/src/app/admin/page.tsx`
- **Description:** Build student registration/login with BMSIT institutional domain verification, and an admin dashboard tracking system CPU/RAM, active render jobs, and campus storage quotas.

---

## 🔍 Verification & Acceptance Criteria

1. **Visual Quality:** Theme adheres strictly to charcoal midnight (`#0B0D13`), champagne-gold (`#E5B869`), and electric cyan (`#38BDF8`). No default unstyled HTML or basic templates.
2. **Interactive Timeline:** Play/Pause, scrubbing, timecode display, zoom in/out, and clip selection work fluidly with active playhead synchronization.
3. **Multi-Track Representation:** Displays 5 distinct tracks (V1, V2, A1, A2, T1) with accurate duration proportions and audio waveforms.
4. **Color Grading Simulation:** Selecting "Golden Hour" or "Teal & Orange" immediately updates the visual appearance of the video canvas preview.
5. **Aspect Ratio Conforming:** Toggling 16:9, 9:16, 1:1, or 21:9 dynamically updates the video viewport frame mask.
6. **AI Director Drawer:** Typing an instruction or clicking a preset ("Deepavali Festive") simulates timeline modifications with undo/redo support.
7. **Export Experience:** Triggering Export displays a realistic step-by-step rendering progress sequence (Analysis -> Filtergraph -> Encoding -> Real MP4 ready) with download action.

---

## 🚀 Execution Command

To execute this plan end-to-end, run:
```bash
/gsd-execute-phase 1
```
