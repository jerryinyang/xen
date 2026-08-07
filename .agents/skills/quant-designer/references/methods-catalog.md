# Methods Catalog

Preferred statistical methods organised by analysis type. Use this catalog when designing analysis plans. Methods are ordered by preference (simplest first within each category).

---

## Descriptive Methods (Always Include)

| Method | Use When | Output | Notes |
|--------|----------|--------|-------|
| Summary statistics (mean, median, std, min, max, quartiles) | Always — baseline description of any feature | Table | Report sample size (n) |
| Histogram with KDE overlay | Understanding distribution shape | Plot | Use enough bins (≥ 30) to see shape |
| Box plot with outliers | Comparing distributions across groups | Plot | Shows median, IQR, whiskers, outliers |
| Time-series line plot | Temporal patterns, sequential dependencies | Plot | Use for features that evolve over time |

## Rank-Based / Non-Parametric Tests

| Method | Use When | Output | Assumptions |
|--------|----------|--------|-------------|
| Spearman rank correlation | Testing monotonic relationship between two continuous variables | ρ coefficient, p-value | None on distribution shape |
| Mann-Whitney U test | Comparing central tendency of two independent groups | U statistic, p-value, effect size | Independent observations |
| Wilcoxon signed-rank test | Comparing paired/matched observations | W statistic, p-value | Symmetric differences |
| Kruskal-Wallis test | Comparing 3+ independent groups | H statistic, p-value | Independent observations |
| Permutation test | Any hypothesis where you can define a test statistic | Empirical p-value, null distribution | Exchangeability under null |

## Bootstrap / Resampling Methods

| Method | Use When | Output | Notes |
|--------|----------|--------|-------|
| Bootstrap confidence interval | Estimating uncertainty of any statistic | CI (lower, upper) + seed range | `xen.evaluation.block_bootstrap_ci`: circular block bootstrap, ≥10,000 resamples × 5-seed battery. Effective block capped < n (no zero-width CI on sparse strata, INFR-004/L-20). For verdict-bearing reads, co-declare a `block_sensitivity` sweep (½×/1×/2×) and, where the mean may be outlier-driven, a `trimmed_mean`/median CI. Report "CI excludes zero", not a p-value. |
| Bootstrap hypothesis test | When analytical p-values are unreliable | Empirical p-value | Resample under null hypothesis |
| Cross-validation | Assessing model stability | Mean score, std across folds | Use chronological CV for time-series |

## Robust Parametric Methods (Use Only with Cross-Validation)

| Method | Use When | Output | Required Cross-Validation |
|--------|----------|--------|--------------------------|
| Pearson correlation | Testing linear relationship, data approximately normal | r coefficient, p-value | Spearman rank correlation |
| OLS regression | Estimating linear effect size | Coefficients, R², p-values | Rank-based regression or permutation test |
| t-test | Comparing means of two groups, approximately normal | t statistic, p-value, Cohen's d | Mann-Whitney U test |

---

## Method Selection by Analysis Type

### Correlation Analysis

| Question | Primary Method | Backup |
|----------|---------------|--------|
| "Are A and B related?" | Spearman ρ | Scatter plot + visual inspection |
| "How strong is the relationship?" | Spearman ρ with bootstrap CI | Partial correlation controlling for C |
| "Does the relationship change across conditions?" | Stratified Spearman by group | Interaction test in rank regression |

### Distribution Analysis

| Question | Primary Method | Backup |
|----------|---------------|--------|
| "What does the distribution look like?" | Histogram + summary stats | KDE plot |
| "Are two distributions different?" | Mann-Whitney U or KS test | Overlaid histograms |
| "Is the distribution symmetric / normal?" | Q-Q plot + skewness/kurtosis | Formal normality test (but treat with skepticism) |

### Temporal / Sequential Analysis

| Question | Primary Method | Backup |
|----------|---------------|--------|
| "Does A at time N predict B at time N+1?" | Lagged Spearman with bootstrap CI | Rolling window analysis |
| "Is there autocorrelation?" | Autocorrelation function (ACF) plot | Ljung-Box test (but note: assumes stationarity) |
| "Do patterns change over time?" | Stratified analysis by time period | Rolling correlation |

### Mean-Reversion Tests

| Question | Primary Method | Backup |
|----------|---------------|--------|
| "Is there mean reversion?" | Hurst exponent (H < 0.5) | Runs test |
| "Does overshoot predict reversal?" | Spearman(overshoot, next_magnitude) with bootstrap CI | Conditional probability analysis |
| "How fast does mean reversion occur?" | Half-life estimation from AR(1) | Distribution of return times |

### Volatility Analysis

| Question | Primary Method | Backup |
|----------|---------------|--------|
| "Is there volatility clustering?" | Autocorrelation of squared returns | Stratified variance by period |
| "Does high volatility predict more high volatility?" | Spearman(vol_t, vol_t+1) with bootstrap CI | GARCH model (but note: assumes stationarity) |

---

## Methods to Avoid

| Method | Why Avoid | Alternative |
|--------|-----------|-------------|
| Standard t-test without cross-validation | Assumes normality, constant variance | Mann-Whitney U + Spearman |
| OLS without robustness checks | Assumes normality, homoskedasticity, independence | Non-parametric regression + permutation test |
| ANOVA without cross-validation | Assumes normality, equal variance | Kruskal-Wallis + permutation test |
| GARCH / ARCH models | Assumes stationarity, specific functional form | Empirical volatility clustering test |
| ADF unit root test | Assumes specific data-generating process | Visual inspection of time-series + rolling statistics |
| Sharpe ratio | Assumes normal returns, penalises upside volatility | Sortino ratio or custom metric |
