# Iconography Audit & Usage Map

**Date**: 2026-02-04
**Status**: Remediation Complete
**Objective**: Map all current icon usage and identify deviations from the [Iconography Governance](./iconography.md).

## 1. Global Navigation (Sidebar)

| Section | Label | Current Icon | Status | Alignment Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Brand** | DevBridge | `Terminal` | ✅ Aligned | Matches technical/dev focus. |
| **Nav** | Chat | `MessageSquare` | ✅ Aligned | Standard chat representation. |
| **Nav** | Dashboard | `LayoutDashboard` | ✅ Aligned | |
| **Nav** | Times | `Users` | ✅ Aligned | |
| **Nav** | Métricas | `BarChart3` | ✅ Aligned | Preferred over `Activity` for deep metrics. |
| **Nav** | Relatórios | `FileText` | ✅ Aligned | |
| **Nav** | Configurações | `Settings` | ✅ Aligned | |
| **Action** | Sair | `LogOut` | ✅ Aligned | Uses semantic error color (Red). |

## 2. Module: Chat

| Component | Context | Current Icon | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Sidebar Action** | New Chat | `MessageSquarePlus` | ✅ Fixed | Unified with Top Bar. |
| **Top Bar** | New Chat | `MessageSquarePlus` | ✅ Aligned | More specific than generic Plus. |
| **Input** | Send | `Send` (PaperPlane) | ✅ Aligned | |
| **Filter** | Product | `Layers` | ✅ Aligned | |
| **Filter** | Teams | `Users` | ✅ Aligned | |
| **Filter** | Projects | `Folder` | ✅ Aligned | |
| **Filter** | Period | `Calendar` | ✅ Aligned | |
| **AI** | Suggestion | `Sparkles` | ✅ Aligned | Standard AI magic semantics. |
| **RAG** | Active | `Circle` (Green Dot) | ✅ Aligned | |

## 3. Module: Dashboard & Metrics (DORA)

| Metric | Context | Current Icon | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Frequency** | Deployment | `TrendingUp` | ✅ Aligned | Good motion semantic. |
| **Lead Time** | Time to Deploy | `Clock` | ✅ Aligned | |
| **Failure Rate** | Change Failure | `AlertTriangle` | ✅ Aligned | Clear warning semantic. |
| **MTTR** | Recovery Time | `RefreshCw` | ✅ Fixed | Distinct from Lead Time `Clock`. |
| **Activity** | PR Merged | `GitMerge` | ✅ Aligned | |
| **Activity** | Timestamp | `Clock` | ✅ Aligned | |
| **Repo** | ID | `Hash` | ✅ Aligned | |

## 4. Module: Reports

| Component | Context | Current Icon | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Selection** | Summary | `BarChart3` | ✅ Fixed | Replaced emoji. |
| **Selection** | Technical | `Settings` | ✅ Fixed | Replaced emoji. |
| **Selection** | Custom | `TrendingUp` | ✅ Fixed | Replaced emoji. |
| **Action** | Generate | `Plus` | ✅ Aligned | |
| **Tab** | History | `Clock` | ✅ Aligned | |
| **Tab** | Templates | `FileText` | ✅ Aligned | |

## 5. Module: Teams & Settings

| Component | Context | Current Icon | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **Empty State** | Generic | `Users` | ⚠️ Overloaded | Use specific empty states: `UserX` for members, `Inbox` for messages. |
| **Integration** | Integration | `Zap` | ✅ Aligned | |
| **Action** | Sync | `RefreshCw` | ✅ Aligned | |
| **Action** | Link | `ExternalLink` | ✅ Aligned | |

## Action Plan
1.  [x] **Replace Emojis in Reports**: Switch to Lucide icons (`PieChart`, `Cpu`, `LineChart`) to strictly enforce the "No Emojis" design rule.
2.  [x] **Differentiate MTTR**: Change MTTR icon to `RefreshCw` to visually distinguish from Lead Time (`Clock`).
3.  [x] **Unify "New Chat"**: adopt `MessageSquarePlus` consistently.
4.  [ ] **Refine Empty States**: Do not default to `Users` for everything. (Future Refinement)
