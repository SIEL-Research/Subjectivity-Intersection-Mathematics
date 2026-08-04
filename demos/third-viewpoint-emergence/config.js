export const config = {
  registeredSeed: 12005006,
  interventionStateIndex: 3,
  modes: {
    quick: {
      label: "Live",
      hiddenDimension: 8,
      symbolClasses: 4,
      seedCount: 1,
      randomControls: 16,
      epochs: 72,
      trainEpisodes: 64,
      validationEpisodes: 48,
      interventionEpisodes: 32,
      exchangeEpisodes: 32,
      learningRate: 0.012
    }
  },
  sequence: { inputSteps: 1, interactionSteps: 2, delaySteps: 3 },
  thresholds: {
    taskBothCorrectMin: 0.45,
    independentRelationRatioMax: 0.25,
    bilateralCeIncreaseMin: 0.0001,
    randomPercentileMin: 0.75,
    crossPairDegradationMin: 0.0001,
    transportedFractionMin: 0.05,
    transportTransitionsRequired: 2,
    supportChecksRequired: 6,
    partialChecksRequired: 3,
    gradientNormAbort: 1000
  },
  thresholds006A: {
    taskBothCorrectMin: 0.45,
    dualComponentMax: 1e-10,
    interactingComponentMin: 0.005,
    bilateralSupportMin: 0.5,
    transportedFractionMin: 0.05,
    transportTransitionsRequired: 2,
    bilateralOutputResponseMin: 0.5,
    crossPairDegradationMin: 0.0001,
    reconstructionErrorMax: 1e-8,
    partialChecksRequired: 4
  },
  numericPrecision: "Float64Array computation; exported values rounded only for display"
};
