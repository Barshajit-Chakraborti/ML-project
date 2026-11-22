# Medicinal Plant Identification from Leaf Images

A deep-learning system that identifies **20 medicinal plant species** from a photograph of a leaf. An ImageNet-pretrained **EfficientNet-B0** is fine-tuned on public leaf datasets, and the trained model is served through a **Django REST API** that returns the three most likely species with confidence scores and a safety disclaimer.

> Final-year B.Tech project, Department of Computer Science and Engineering, National Institute of Technology Agartala.
> **[Add: team members, supervisor, year]**

> **This is an identification aid, not medical advice.** Never eat, apply or use a plant based on this result. Several toxic plants resemble medicinal ones. Always have a result verified by a qualified expert.

---

## Contents

- [Key results](#key-results)
- [Features](#features)
- [How it works](#how-it-works)
- [Supported plants](#supported-plants)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [API reference](#api-reference)
- [Data and the leakage-safe pipeline](#data-and-the-leakage-safe-pipeline)
- [Training and evaluation](#training-and-evaluation)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Team, acknowledgements and licence](#team-acknowledgements-and-licence)

---

## Key results

Measured once on **445 held-out test images** (about 22 per species) taken from the public datasets:

| Metric | Value |
|---|---|
| Top-1 accuracy | **97.5%** |
| Top-3 accuracy | **99.6%** |
| Macro-F1 | **0.975** |
| Weakest class | papaya (F1 0.93) |
| Misclassified images | 11 of 445 |

The 95% uncertainty on the accuracy is roughly ±1.5 percentage points, and with about 20 test images per class one mistake moves a class score by about 5 points.

> **Read this before quoting the numbers.** The test images come from the same public datasets as the training images (similar backgrounds, cameras and photographers). The figures show the model separates these images well; they do **not** show how it performs on photographs taken in a garden or with another phone. A separate field test on our own photographs is described in the [roadmap](#roadmap).

## Features

- Upload a leaf photo and get the **top 3 species** with confidence scores
- A `matched` flag that warns when the model is not confident
- Plant catalogue with search, and a detail view per plant
- Optional location (latitude and longitude) saved with each identification
- Feedback endpoint: a user confirms or rejects a result; a rejected upload is deleted
- Health endpoint that reports whether the model is loaded
- Reproducible data and training pipeline, with a post-split leakage audit

## How it works

```mermaid
flowchart LR
    A[Leaf photo] --> B[Django API]
    B --> C[Fix orientation, resize 224x224, normalise]
    C --> D[EfficientNet-B0]
    D --> E[Softmax: top-3 class positions]
    E --> F[Look up plants by class_index]
    F --> G[JSON: predictions, matched flag, disclaimer]
```

The model outputs a **position** in its class list (0 to 19). The API converts that position to a database row through `Plant.class_index`, so **`class_index` must follow the class order stored inside the checkpoint**. See [Keeping the model and the database in sync](#keeping-the-model-and-the-database-in-sync).

## Supported plants

| # | Class id | Scientific name |
|---|---|---|
| 0 | aloevera | *Aloe vera* |
| 1 | amla | *Phyllanthus emblica* |
| 2 | amruthaballi | *Tinospora cordifolia* |
| 3 | ashwagandha | *Withania somnifera* |
| 4 | betel | *Piper betle* |
| 5 | brahmi | *Bacopa monnieri* |
| 6 | castor | *Ricinus communis* |
| 7 | catharanthus | *Catharanthus roseus* |
| 8 | curry | *Murraya koenigii* |
| 9 | drumstick | *Moringa oleifera* |
| 10 | ekka | *Calotropis gigantea* |
| 11 | guava | *Psidium guajava* |
| 12 | insulin | *Costus igneus* |
| 13 | jamun | *Syzygium cumini* |
| 14 | mint | *Mentha* |
| 15 | neem | *Azadirachta indica* |
| 16 | papaya | *Carica papaya* |
| 17 | parijata | *Nyctanthes arbor-tristis* |
| 18 | pomegranate | *Punica granatum* |
| 19 | tulsi | *Ocimum tenuiflorum* |

Class ids and their order come from the trained checkpoint (alphabetical). The model recognises **only these 20 species**: for any other plant it still names one of them, which is why the confidence flag exists.

## Repository structure

**[Adjust to match your actual repository.]**

```
.
├── requirements.txt
├── ml/                      Training pipeline (scripts below)
└── root/                    Django project (manage.py lives here)
    ├── api/                 REST views, serializers, inference.py, retrain.py
    ├── plants/              Models (Plant, Identification, Feedback), management commands
    ├── ml_models/           Trained weights and classifier code (weights are NOT in git)
    ├── data/                Class map
    ├── frontend/            Web client
    ├── media/               Uploaded photos (NOT in git)
    └── root/                Django settings and URL configuration
```

| ML script | Purpose |
|---|---|
| `ml/inspect_raw.py` | Pre-flight check of raw datasets: sizes, duplicates, pre-augmentation, overlap between datasets |
| `ml/make_class_map.py` | Draft a class map and merge the same species across datasets |
| `ml/prune_class_map.py` | Keep only chosen classes (`--only`), rename classes (`--rename`) |
| `ml/prepare_data.py` | Build train/val/test sets: de-duplicate, group-aware split, standardise |
| `ml/audit_leakage.py` | Remove val/test images that duplicate a training image |
| `ml/train.py` | Two-phase fine-tuning of EfficientNet-B0 |
| `ml/report.py` | Training curves, per-class scores, confusion matrix, error list |
| `ml/common.py` | Shared model builder, transforms and device selection |

## Getting started

### Requirements

- Python 3.13 (3.11 or newer should work)
- An NVIDIA GPU with CUDA is optional: the API runs on CPU, and a GPU speeds up training
- Git

### Install

```bash
git clone <repository-url>
cd <repository-folder>

python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate          # Linux / macOS

pip install -r requirements.txt
```

`requirements.txt` should include Django, Django REST Framework, Pillow, NumPy, PyTorch and torchvision. For GPU training install the CUDA build of PyTorch from <https://pytorch.org/get-started/locally/> first.

### Add the trained model

The weights are not stored in git. **[Add: download link or instructions.]** Place the checkpoint at `root/ml_models/efficientnet_b0_best.pt` (or set the path in `settings.py`: **[Add: setting name]**). It stores the weights, the architecture name, the input size and the ordered class list.

### Set up the database and run

```bash
cd root
python manage.py migrate
python manage.py load_class_map       # create/refresh Plant rows from the class map
python manage.py runserver
```

### Keeping the model and the database in sync

`Plant.class_index` must equal the position of that plant in the checkpoint's class list. **After every retraining, or whenever the species list changes, regenerate it** and then check that every class resolves to a plant:

```bash
python manage.py load_class_map
```

Never match a prediction to a database primary key directly, and do not reuse a class map from a different model. A mismatch makes the API return the wrong plant for a prediction.

(On Windows PowerShell write `curl.exe`, because plain `curl` is an alias for another command.)

## API reference

**[Verify every path against `api/urls.py`.]**

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/identify/` | Upload a leaf photo (form field `image`, optional `latitude`, `longitude`) and get the top-k species |
| GET | `/api/identifications/<id>/` | Fetch a saved identification with its photo URL |
| GET | `/api/plants/?search=` | List plants; search by scientific, common or local name or slug |
| GET | `/api/plants/<id>/` | Details of one plant |
| POST | `/api/feedback/` | JSON `{identification_id, plant_id, is_correct}`; an incorrect result deletes the upload |
| GET | `/api/health/` | Model status and number of plants in the database |

**Example response of `POST /api/identify/`:**

```json
{
  "id": 12,
  "predictions": [
    {"plant_id": 15, "scientific_name": "Azadirachta indica", "common_name": "Neem", "confidence": 0.9312},
    {"plant_id": 11, "scientific_name": "Psidium guajava", "common_name": "Guava", "confidence": 0.0341},
    {"plant_id": 9,  "scientific_name": "Moringa oleifera", "common_name": "Drumstick", "confidence": 0.0102}
  ],
  "matched": true,
  "disclaimer": "Prototype for learning only. Never eat or use a plant based on this result."
}
```

`matched` is `true` when the top confidence reaches `CONFIDENCE_THRESHOLD`.

**Errors:** `400` no image, not a valid image, or larger than `MAX_UPLOAD_MB`; `404` the prediction has no matching plant in the database (run the class map command); `503` the model is not available.

**Privacy:** uploaded photos and optional coordinates are stored on the server. A user who marks a result as incorrect causes that photo and its record to be deleted. Do not deploy publicly without a privacy notice and authentication.

## Data and the leakage-safe pipeline

The datasets are **not** included in this repository. **[Add: names, authors, links and licences of the datasets.]**

The first version of this project reported high accuracy only because its training data were screenshots of video frames, so near-identical frames sat in both the training and test sets. The data pipeline was therefore rebuilt around three ideas:

1. **Inspect before training.** `inspect_raw.py` hashes every image (including flipped and rotated variants) and reports duplicate rates and overlap between datasets. It showed that the available datasets overlap heavily and that one is a pre-augmented copy of another, which was excluded.
2. **Split by group, never by image.** Images with the same observation or plant id in the file name, or within 6 bits of each other by a 64-bit difference hash, stay in the same split. Near-identical copies shared between datasets (within 2 bits) are kept once.
3. **Audit the result.** `audit_leakage.py` compares every validation and test image with all training images and removes true duplicates (within 2 bits). A looser threshold flags coincidental matches between different species, so the strict one is used for deletion.

Limitation: the splitting hash is not invariant to flips and rotations, so pre-augmented datasets are excluded instead of filtered.

## Training and evaluation

| Setting | Value |
|---|---|
| Model | EfficientNet-B0, ImageNet-pretrained, 224 × 224 input, 20 outputs |
| Phases | 2 epochs classifier only (learning rate 1e-3), then all layers (1e-4, cosine annealing) |
| Optimiser / loss | AdamW (weight decay 1e-4), cross-entropy with label smoothing 0.1 |
| Batch size / epochs | 16 / up to 25 with early stopping (patience 4) |
| Class balance | Weighted sampler |
| Model selection | Best validation macro-F1 |
| Seed | 42 |
| Hardware | NVIDIA RTX 3050 laptop GPU (4 GB), about 6 minutes |

To reproduce (from the folder that holds `ml/`, `data/` and `docs/`):

```bash
python ml/make_class_map.py data/raw/<datasetA> data/raw/<datasetB> --out docs/class_map_draft.csv
python ml/prune_class_map.py --map docs/class_map_draft.csv --out docs/class_map_final.csv --only <20 class ids>
python ml/prepare_data.py --raw data/raw --map docs/class_map_final.csv --out data/processed
python ml/audit_leakage.py --root data/processed --max-ham 2 --delete
python ml/train.py --arch efficientnet_b0 --epochs 25 --epoch-size 999999 --bs 16 --workers 2 --out models/run20
python ml/report.py --ckpt models/run20/efficientnet_b0_best.pt --history models/run20/efficientnet_b0_history.csv --out reports/run20
```

`report.py` writes training curves, a per-class metrics table, a confusion matrix, the most frequent confusions and the list of misclassified images. Add `--root data/field_test` to score your own photographs.

## Limitations

- **Same-source test set.** The reported accuracy is on held-out photographs from the training datasets, not on field photographs.
- **Domain shift.** The datasets mostly show single leaves on plain backgrounds; whole plants outdoors are under-represented. An earlier version of the model misclassified a phone photograph of an aloe vera plant.
- **Closed set.** Only 20 species are recognised, and any other plant is still assigned to one of them. The confidence flag is a first safeguard and has not yet been tuned on field data.
- **Overlapping datasets.** Duplicates were removed, but near-copies with different cropping may remain.
- **Unverified labels.** Labels come from the source datasets. Four regional names (amruthaballi, brahmi, ekka, insulin) still need their scientific identity confirmed.
- **No medicinal information from the model.** The model identifies; it does not advise. Plant descriptions in the database may not come from verified sources.
- **Small test sets per class** (about 20 images) and a single training run.