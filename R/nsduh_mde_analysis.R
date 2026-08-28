# Major Depressive Episode and Substance Use in the United States
# National Survey on Drug Use and Health (NSDUH), 2022-2024
#
# The analysis pipeline in R. The original was written as an R Markdown document;
# this is the same code path, cleaned for publication and with the survey design
# added in Part 6.
#
# The NSDUH public-use files are about 1.1 GB and are not distributed with this
# repository. Download them from SAMHSA and set DATA_DIR:
#   https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health

DATA_DIR <- "path/to/nsduh"

library(tidyverse)
library(VIM)          # missingness visualisation
library(factoextra)   # PCA and clustering plots
library(caret)        # cross-validation and tuning
library(rpart)        # classification tree
library(rpart.plot)
library(survey)       # complex survey design, Part 6

# ---------------------------------------------------------------------------
# Part 1. Read and pool the survey years
# ---------------------------------------------------------------------------
# Each file is one year, tab separated, roughly 2,650 columns. Only a handful are
# needed, and the three design variables matter as much as the analysis ones:
#   ANALWT2_C  the analysis weight
#   VESTR_C    the variance estimation stratum
#   VEREP      the variance estimation replicate
vars <- c("IRSEX", "CATAG6", "INCOME", "HEALTH2",
          "IRALCRC", "IRMJRC", "CIGMON", "AMDEYR", "AMIPY",
          "ANALWT2_C", "VESTR_C", "VEREP")

read_year <- function(year) {
  path <- file.path(DATA_DIR, sprintf("NSDUH_%d_Tab.txt", year))
  d <- read.delim(path)[, vars]
  d$YEAR <- year
  d
}
df <- bind_rows(lapply(c(2022, 2023, 2024), read_year))

# Pooling years: the weight must be divided by the number of years, or the pooled
# estimates describe a population three times too large.
df$WT <- df$ANALWT2_C / 3

# ---------------------------------------------------------------------------
# Part 2. Recode
# ---------------------------------------------------------------------------
df <- df %>% mutate(
  ALC_PASTMO = as.integer(IRALCRC == 1),
  MJ_PASTMO  = as.integer(IRMJRC  == 1),
  CIG_PASTMO = as.integer(CIGMON  == 1),
  MDE        = ifelse(AMDEYR %in% c(1, 2), as.integer(AMDEYR == 1), NA),
  AMI        = ifelse(AMIPY  %in% c(1, 2), as.integer(AMIPY  == 1), NA),
  HEALTH     = ifelse(HEALTH2 %in% 1:4, HEALTH2, NA)
)

# The adult depression question is not asked of 12-17 year olds (CATAG6 == 1), so
# dropping missing MDE removes them entirely. That is a restriction on the
# population, not missing data: the analysis is of adults 18 and over.
cat("adolescents in the pooled file:", sum(df$CATAG6 == 1), "\n")
nsduh <- df %>% filter(!is.na(MDE), !is.na(HEALTH))
cat("analysis sample:", nrow(nsduh), "\n")

# ---------------------------------------------------------------------------
# Part 3. Missingness and descriptives
# ---------------------------------------------------------------------------
VIM::aggr(df[, c("IRSEX","CATAG6","INCOME","HEALTH","ALC_PASTMO",
                 "MJ_PASTMO","CIG_PASTMO","MDE","AMI")],
          numbers = TRUE, prop = FALSE, sortVars = TRUE)

# Unweighted prevalence: a property of the sample, not of the country.
nsduh %>% group_by(YEAR) %>%
  summarise(across(c(ALC_PASTMO, MJ_PASTMO, CIG_PASTMO, MDE), ~ mean(.) * 100))

# ---------------------------------------------------------------------------
# Part 4. PCA and k-means
# ---------------------------------------------------------------------------
pca_vars <- c("ALC_PASTMO","MJ_PASTMO","CIG_PASTMO","IRSEX","CATAG6","INCOME","HEALTH")
X  <- scale(nsduh[, pca_vars])          # standardise: the variables are on different scales
pc <- prcomp(X)
fviz_eig(pc)                            # scree plot
scores <- pc$x[, 1:3]

set.seed(1)
fviz_nbclust(scores[sample(nrow(scores), 25000), ], kmeans, method = "wss", k.max = 8)
km <- kmeans(scores, centers = 4, nstart = 10)
nsduh$cluster <- km$cluster

nsduh %>% group_by(cluster) %>%
  summarise(n = n(), across(c(ALC_PASTMO, MJ_PASTMO, CIG_PASTMO, MDE), ~ mean(.) * 100))

# ---------------------------------------------------------------------------
# Part 5. Predicting MDE
# ---------------------------------------------------------------------------
model_vars <- pca_vars
glm_data <- nsduh[, c(model_vars, "MDE")]
glm_data$MDE <- factor(ifelse(glm_data$MDE == 1, "Yes", "No"), levels = c("No", "Yes"))

set.seed(1)
ctrl <- trainControl(method = "cv", number = 10, classProbs = TRUE,
                     summaryFunction = twoClassSummary)
lasso_fit <- train(x = glm_data[, model_vars], y = glm_data$MDE,
                   method = "glmnet", metric = "ROC", trControl = ctrl,
                   tuneGrid = expand.grid(alpha = 1, lambda = 10^seq(-4, 0, length = 20)))

# The outcome is imbalanced at roughly 7.9 to 1. At the default 0.50 cut-off the
# model almost never predicts the minority class, so accuracy looks high and kappa
# is near zero. Inspect the trade-off rather than reporting accuracy alone.
thresholder(lasso_fit, threshold = seq(0.05, 0.5, by = 0.05),
            final = TRUE, statistics = "all")

tree <- rpart(MDE ~ ., data = glm_data, method = "class",
              cp = 0.001, control = rpart.control(maxdepth = 4))
rpart.plot(tree, type = 2, extra = 104)

# ---------------------------------------------------------------------------
# Part 6. The survey design
# ---------------------------------------------------------------------------
# Everything above treats the data as a simple random sample. NSDUH is a stratified
# multistage sample, so unweighted percentages describe the respondents rather than
# the population, and standard errors computed without the design are too small.
options(survey.lonely.psu = "adjust")
des <- svydesign(ids = ~VEREP, strata = ~VESTR_C, weights = ~WT,
                 data = nsduh, nest = TRUE)

# Population estimates, with design-correct standard errors.
svymean(~ALC_PASTMO + MJ_PASTMO + CIG_PASTMO + MDE, des)
svyby(~MDE, ~CATAG6, des, svymean)

# The same logistic regression, design aware. Compare these standard errors with
# the naive ones: they are substantially larger.
svyglm(MDE ~ ALC_PASTMO + MJ_PASTMO + CIG_PASTMO + IRSEX + CATAG6 + INCOME + HEALTH,
       design = des, family = quasibinomial())
