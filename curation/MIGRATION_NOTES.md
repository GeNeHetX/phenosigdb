# Migration Notes

This document summarizes the source material migrated from `CancerRNASig`.

## Source inventory

| Source folder | Publication | Signature groups | Species | Proposed metadata |
| --- | --- | --- | --- | --- |
| `CAF.Dominguez20` | Dominguez.etal;PMID:31699795 | 3 | human | fibroblast, cancer, PDAC |
| `CAF.Elyada19` | Elyada.etal;PMID:31197017 | 2 | human | fibroblast, cancer, PDAC |
| `CAF.Kieffer20` | Kieffer.etal;PMID:32434947 | 8 | human | fibroblast, cancer, PDAC |
| `CAF.Neuzillet22` | Neuzillet.etal;PMID:36102377 | 4 | human | fibroblast, cancer, PDAC |
| `CCCA.Gavish23` | Gavish.etal;PMID:37258682 | 41 | human | tumor, cancer, cholangiocarcinoma |
| `CCK.Sia13` | Sia.etal;PMID:23295441 | 2 | human | epithelial, cancer, cholangiocarcinoma |
| `CCK_STIM.Serrano23` | MartinSerrano.etal;PMID:35584893 | 5 | human | epithelial, cancer, cholangiocarcinoma |
| `ECM.Helms22` | Helms.etal;PMID.34548310 | 1 | human | stromal, cancer, PDAC |
| `FibroAtlas.Gao24` | Yang-Gao.etal;PMID:39303725 | 20 | human | fibroblast, physiology, normal |
| `HCC.Petitprez19` | Petitprez.etal;DOI:10.1101/540005 | 73 | human | tumor, cancer, HCC |
| `IMMU.Rodrigues18` | Rodrigues.etal;PMID:30179225 | 2 | human | immune, unknown, unknown |
| `IMMU_MCPcounter.Becht16` | Becht.etal;PMID:27765066 | 10 | human | immune, unknown, unknown |
| `IMMU_Neutro.Wu24` | Wu.etal;PMID:38447573 | 10 | human | neutrophil, unknown, unknown |
| `IMMU_Tcell.Chu23` | Chu.etal;PMID:37248301 | 8 | human | T_cell, unknown, unknown |
| `IMMU_monoMac.Mulder21` | K.Mulder;PMID:34331874 | 17 | human | macrophage, unknown, unknown |
| `Organoid_Atlas.Xu25` | Xu.etal;PMID:40355592 | 48 | human | epithelial, organoid, unknown |
| `PDAC.Bailey16` | Bailey.etal;PMID:26909576 | 4 | human | tumor, cancer, PDAC |
| `PDAC.ChanSengYue20` | Chan-Seng-Yue.etal;PMID:31932696 | 12 | human | tumor, cancer, PDAC |
| `PDAC.Hwang22` | Hwang.etal;PMID.35902743 | 18 | human | tumor, cancer, PDAC |
| `PDAC.Maurer18` | Maurer.etal;PMID:30658994 | 2 | human | tumor, cancer, PDAC |
| `PDAC.Moffitt15` | Moffitt.etal;PMID:26343385 | 14 | human | tumor, cancer, PDAC |
| `PDAC.Puleo18` | Puleo.etal;PMID:30165049 | 10 | human | tumor, cancer, PDAC |
| `PDAC_PDAssigner.Colisson11` | Collisson.etal;PMID:21460848 | 3 | human | tumor, cancer, PDAC |
| `PDAC_PDXph1.Nicolle17` | Nicolle.etal;PMID:29186684 | 2 | human | tumor, cancer, PDAC |
| `SPEM.Bockerstett20` | K.Bockerstett;PMID:31481545 | 15 | human | epithelial, physiology, normal |
| `Stroma.Grunwald21` | Grunwald.etal;PMID:34644529 | 2 | human | stromal, cancer, PDAC |
| `scADM_Mouse.Ma21` | Z.Ma.etal;PMID:34695382 | 11 | mouse | epithelial, physiology, normal |
| `scDuctalPancreas_Mouse.Fernandez24` | A.Fernandez;PMID:38908487 | 23 | mouse | epithelial, physiology, normal |
| `scGC.Kim22` | J.Kim;PMID:35087207 | 7 | human | tumor, cancer, gastric_cancer |
| `scGI.Busslinger21` | G.Busslinger.etal;PMID:33691112 | 35 | human | epithelial, physiology, normal |
| `scGastricTME.Sathe20` | A.Sathe;PMID:32060101 | 3 | human | tumor, cancer, gastric_cancer |
| `scIBD.Nie23` | H.Nie;PMID:38177426 | 96 | human | immune, inflammation, IBD |
| `scPancreas_Mouse.Schlesinger20` | Y.Schlesinger;PMID:32908137 | 14 | mouse | epithelial, physiology, normal |
| `siNETs.Patte25` | C.Patte;PMID:40038310 | 4 | human | tumor, cancer, siNETs |

## Notes

- The model objects and predictive artifacts from `CancerRNASig` were intentionally excluded.
- The migrated content is limited to gene-set signatures.
- Species and metadata are intentionally coarse and should remain easy to curate.
- One upstream subgroup, `scGI.Busslinger21_duodenum_normal_cells_single_cell.ADH4_cells`, had zero genes in the exported source material and is not representable in the one-row-per-gene canonical table.
