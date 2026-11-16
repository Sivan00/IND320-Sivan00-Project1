# Project 3 – feedback update

This folder contains my follow-up to the feedback on weather sampling. The original submitted notebook, PDF and screencast remain linked from the [Project 3 overview](../README.md).

## What changed

- East is the combined NVE region RS + RØ, West is RV, and North is RM + RN. I sample 1,000 coordinates **inside each combined region**, using a fixed seed and an equal-area projection. These NVE administrative polygons are an approximation to precipitation regions, not exact catchments.
- Electricity bidding zones NO1–NO5 are separate polygons. The weather page uses the selected electricity zone, with a reproducible sample of 1,000 points in that zone.
- The weather downloader can now accept all 1,000 sampled locations. The app offers 5, 25, 100 or 1,000; five remains the quick default. Larger downloads require an explicit button press because they can be slow and reach the API limit.
- Downloads are processed in batches. A batch is checked for every requested location and hour before it contributes to the mean. Successful batch summaries are cached for up to seven days in memory and, when writable, in the local ignored `.cache/` folder so a retry can continue later. Cloud redeployments or unavailable storage can clear the cache. Incomplete downloads do not produce an apparent full-sample average.
- The [feedback notebook](IND320_project_3_feedback_update.ipynb) checks the combined-region boundaries and compares parameter settings using clearly labelled synthetic data.

## What is not yet completed

The submitted NO3 analysis used **five locations for 2024**, not 1,000. On 16 November 2026 an initial one-day request reached the API limit. A slower retry succeeded for **all 1,000 NO3 points on 1 January 2024**; the [24 hourly averages](NO3_1000_points_2024-01-01.json) are saved in this folder. They are aggregates, not the individual location responses. A complete 1,000-location year has **not been downloaded or analysed** in this update. The code can retry the larger request when quota permits, but Open-Meteo's free quota may prevent a complete full-year request in one day. Do not interpret the existing five-point results as an analysis of all 1,000 points.

The full-year weather API workload and the app's ability to finish that workload remain to be verified with sufficient API capacity. Local tests also simulated 1,000 locations and confirmed that incomplete responses are rejected. A five-location request for the complete year returned 8,784 real hourly observations.

Open-Meteo documents its [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) and [free API request limits](https://open-meteo.com/en/pricing). The updated code and app are on the `project-3-feedback` branch for review; the public app continues to run the version on `main` until the update is merged and deployed.
