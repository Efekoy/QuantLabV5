# SELECTION AUDIT -- mechanical application of the approved rule

Rule: `results/edge_isolation/PROPOSED_FINAL_SELECTION_RULE.md`, SHA-256 `c74000f922a197c025123915ecba1f556077c6fa704cf903bd999784484b3209` (recorded in `integrity/SELECTION_RULE.sha256` BEFORE the selection ran; unchanged).

Eligible clusters (stronger subset, CLEARLY ABOVE NULL or MIXED): **6** (CLEARLY ABOVE NULL 3, MIXED 3). Processing order: Tier 1 before Tier 2, larger first, ties by cluster ID.

| cluster | evidence | members | entry rules | family | instruments | directions | medoid | medoid entry / mgmt robustness | medoid passes robustness | selected | members tried | final status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | CLEARLY ABOVE NULL | 981 | 22 | mean_deviation | NQ 977; ES 4 | long 981 | `Cde07e4a776a3c324` | MODERATE / BROAD_PLATEAU | yes | `C39d55eaa5412f438` | 1 | SELECTED |
| 1 | CLEARLY ABOVE NULL | 632 | 22 | momentum | NQ 632 | both 619; short 13 | `C5e2c4dc9cb997f16` | CLIFF / BROAD_PLATEAU | NO (entry CLIFF) | `C175c690afa915a44` | 46 | SELECTED |
| 2 | CLEARLY ABOVE NULL | 496 | 9 | mean_deviation | NQ 496 | both 496 | `C9b2038870f70e012` | NARROW / BROAD_PLATEAU | yes | `C21fa22c47ad5c1cd` | 2 | SELECTED |
| 3 | MIXED | 298 | 3 | cross_market | NQ 298 | both 221; short 77 | `Cfa58defc877d8ea6` | MODERATE / NO_NEIGHBOURS | yes | `C7162dcd77274b6f3` | 1 | SELECTED |
| 4 | MIXED | 271 | 2 | momentum | NQ 271 | long 232; both 39 | `Cef95b7cf49251506` | MODERATE / NO_NEIGHBOURS | yes | `C3dc5dc6a88e523c7` | 1 | SELECTED |
| 14 | MIXED | 62 | 12 | momentum | NQ 62 | both 54; short 8 | `C1cf9dd8f45bc741e` | BROAD_PLATEAU / MODERATE | yes | `C1cf9dd8f45bc741e` | 2 | SELECTED |

## Per-cluster detail

### Cluster 0 (CLEARLY ABOVE NULL, 981 members, p_size 0.0050, p_entries 0.0100, p_strong 0.0050)
- Robustness filter: 789 eligible members; 192 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `Cde07e4a776a3c324` (centrality 0.7085): passes robustness.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 36 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C39d55eaa5412f438` (centrality 0.7033, central set) -- corr to accepted: none accepted yet -> **ACCEPTED**
- **Final status: SELECTED** -- `C39d55eaa5412f438` (not the medoid: simpler member inside the central set (complexity / management / legs order))

### Cluster 1 (CLEARLY ABOVE NULL, 632 members, p_size 0.0050, p_entries 0.0100, p_strong 0.0050)
- Robustness filter: 555 eligible members; 77 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `C5e2c4dc9cb997f16` (centrality 0.7010): EXCLUDED by the robustness rule (entry robustness CLIFF); the next members in the deterministic ordering were used.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 13 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C0419c67eecb94bf2` (centrality 0.6797, central set) -- corr to accepted: C39d55eaa 0.621 -> **CORRELATION_EXCLUDED (max 0.621 > 0.5)**
  - try 2: `C11d4f2a0b349f8ec` (centrality 0.6822, central set) -- corr to accepted: C39d55eaa 0.646 -> **CORRELATION_EXCLUDED (max 0.646 > 0.5)**
  - try 3: `C2addcd3b3548f658` (centrality 0.6966, central set) -- corr to accepted: C39d55eaa 0.636 -> **CORRELATION_EXCLUDED (max 0.636 > 0.5)**
  - try 4: `C43b0f76616acff08` (centrality 0.6938, central set) -- corr to accepted: C39d55eaa 0.611 -> **CORRELATION_EXCLUDED (max 0.611 > 0.5)**
  - try 5: `C9b4c49137b7ae053` (centrality 0.6804, central set) -- corr to accepted: C39d55eaa 0.608 -> **CORRELATION_EXCLUDED (max 0.608 > 0.5)**
  - tries 6..45: all CORRELATION_EXCLUDED (full list in selection/SELECTION_RESULT.json)
  - try 46: `C175c690afa915a44` (centrality 0.6483, outside central set) -- corr to accepted: C39d55eaa 0.497 -> **ACCEPTED**
- **Final status: SELECTED** -- `C175c690afa915a44` (not the medoid: medoid failed robustness)

### Cluster 2 (CLEARLY ABOVE NULL, 496 members, p_size 0.0050, p_entries 0.0846, p_strong 0.0050)
- Robustness filter: 454 eligible members; 42 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `C9b2038870f70e012` (centrality 0.7420): passes robustness.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 72 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C0d798147fbdeb22c` (centrality 0.7231, central set) -- corr to accepted: C39d55eaa 0.505, C175c690a 0.512 -> **CORRELATION_EXCLUDED (max 0.512 > 0.5)**
  - try 2: `C21fa22c47ad5c1cd` (centrality 0.7279, central set) -- corr to accepted: C39d55eaa 0.494, C175c690a 0.467 -> **ACCEPTED**
- **Final status: SELECTED** -- `C21fa22c47ad5c1cd` (not the medoid: correlation cap)

### Cluster 3 (MIXED, 298 members, p_size 0.0199, p_entries 0.6418, p_strong 0.0199)
- Robustness filter: 296 eligible members; 2 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `Cfa58defc877d8ea6` (centrality 0.7214): passes robustness.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 38 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C7162dcd77274b6f3` (centrality 0.7063, central set) -- corr to accepted: C39d55eaa 0.207, C175c690a 0.249, C21fa22c4 0.243 -> **ACCEPTED**
- **Final status: SELECTED** -- `C7162dcd77274b6f3` (not the medoid: simpler member inside the central set (complexity / management / legs order))

### Cluster 4 (MIXED, 271 members, p_size 0.0249, p_entries 0.9353, p_strong 0.0249)
- Robustness filter: 259 eligible members; 12 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `Cef95b7cf49251506` (centrality 0.8039): passes robustness.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 64 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C3dc5dc6a88e523c7` (centrality 0.7935, central set) -- corr to accepted: C39d55eaa 0.386, C175c690a 0.214, C21fa22c4 0.156, C7162dcd7 0.220 -> **ACCEPTED**
- **Final status: SELECTED** -- `C3dc5dc6a88e523c7` (not the medoid: simpler member inside the central set (complexity / management / legs order))

### Cluster 14 (MIXED, 62 members, p_size 0.3881, p_entries 0.0249, p_strong 0.3881)
- Robustness filter: 48 eligible members; 14 excluded (entry robustness CLIFF / NO_NEIGHBOURS or management robustness CLIFF).
- Medoid `C1cf9dd8f45bc741e` (centrality 0.7192): passes robustness.
- Central set (eligible members within 0.02 of the maximum eligible centrality): 4 members, ordered by entry complexity, management simplicity, legs, candidate_id; then remaining members by descending centrality.
  - try 1: `C101621e0d9d3abec` (centrality 0.7162, central set) -- corr to accepted: C39d55eaa 0.287, C175c690a 0.512, C21fa22c4 0.373, C7162dcd7 0.236, C3dc5dc6a 0.191 -> **CORRELATION_EXCLUDED (max 0.512 > 0.5)**
  - try 2: `C1cf9dd8f45bc741e` (centrality 0.7192, central set) -- corr to accepted: C39d55eaa 0.260, C175c690a 0.483, C21fa22c4 0.350, C7162dcd7 0.189, C3dc5dc6a 0.169 -> **ACCEPTED**
- **Final status: SELECTED** -- `C1cf9dd8f45bc741e`

No cluster was excluded. Correlation cap 0.5 was never raised; no PF, WR, net P&L or recent result was used at any step.
