import type { AxisCandidate, PredictionItem, HistoryItem } from '@/types/prediction';
import type { StatisticsData } from '@/types/statistics';

// サンプル軸候補データ（新仕様対応）
export const sampleAxisCandidates: AxisCandidate[] = [
  {
    axis: 7,
    confidence: 0.92,
    chart_score: 0.88,
    rehearsal_score: 0.94,
    reason: "過去L字パターン類似度94%",
    score: 985,
    source: 'A1', // 欠番補足あり、中心0配置なし
    candidates: {
      box: [
        { number: "147", score: 978, probability: 0.221, reason: "L字配置完全一致", source: 'A1' },
        { number: "079", score: 942, probability: 0.194, reason: "過去類似パターン", source: 'B1' },
        { number: "278", score: 916, probability: 0.176, reason: "リハーサル相関性高", source: 'A1' },
        { number: "357", score: 901, probability: 0.163, reason: "統計的特徴良好", source: 'A1' },
        { number: "670", score: 887, probability: 0.152, reason: "出現周期パターン", source: 'B1' },
      ],
      straight: [
        { number: "174", score: 978, probability: 0.183, reason: "過去類似パターンと94%一致", source: 'A1' },
        { number: "079", score: 942, probability: 0.157, reason: "リハーサル相関性高", source: 'B1' },
        { number: "278", score: 916, probability: 0.141, reason: "L字配置完全一致", source: 'A1' },
        { number: "357", score: 901, probability: 0.132, reason: "統計的特徴良好", source: 'A1' },
        { number: "670", score: 887, probability: 0.125, reason: "出現周期パターン", source: 'B1' },
      ]
    }
  },
  {
    axis: 2,
    confidence: 0.87,
    chart_score: 0.82,
    rehearsal_score: 0.90,
    reason: "リハーサル相関性高",
    score: 952,
    source: 'B1', // 欠番補足なし（0も含めて、すべて欠番補足しない）、中心0配置なし
    candidates: {
      box: [
        { number: "245", score: 967, probability: 0.231, reason: "パターンB最適化パターン", source: 'B1' },
        { number: "278", score: 948, probability: 0.198, reason: "頻出数字候補", source: 'A1' },
        { number: "124", score: 931, probability: 0.183, reason: "統計的特徴良好", source: 'A1' },
        { number: "026", score: 914, probability: 0.171, reason: "0ありパターン特化", source: 'B1' },
        { number: "234", score: 899, probability: 0.162, reason: "連番パターン", source: 'A1' },
      ],
      straight: [
        { number: "245", score: 967, probability: 0.192, reason: "パターンB特有の配置パターン", source: 'B1' },
        { number: "278", score: 948, probability: 0.165, reason: "中心0配置との相関性", source: 'A1' },
        { number: "124", score: 931, probability: 0.148, reason: "統計的特徴良好", source: 'A1' },
        { number: "026", score: 914, probability: 0.139, reason: "0ありパターン特化", source: 'B1' },
        { number: "234", score: 899, probability: 0.131, reason: "連番パターン", source: 'A1' },
      ]
    }
  },
  {
    axis: 5,
    confidence: 0.74,
    chart_score: 0.79,
    rehearsal_score: 0.71,
    reason: "出現周期パターン",
    score: 918,
    source: 'A1', // 欠番補足あり、中心0配置なし
    candidates: {
      box: [
        { number: "145", score: 934, probability: 0.221, reason: "過去類似パターン", source: 'A1' },
        { number: "579", score: 921, probability: 0.194, reason: "統計的特徴良好", source: 'A1' },
        { number: "025", score: 908, probability: 0.182, reason: "補完パターン", source: 'B1' },
        { number: "356", score: 892, probability: 0.173, reason: "周期パターン", source: 'A1' },
      ],
      straight: [
        { number: "154", score: 934, probability: 0.183, reason: "過去類似パターン", source: 'A1' },
        { number: "579", score: 921, probability: 0.157, reason: "統計的特徴良好", source: 'A1' },
        { number: "025", score: 908, probability: 0.145, reason: "補完パターン", source: 'B1' },
        { number: "356", score: 892, probability: 0.138, reason: "周期パターン", source: 'A1' },
      ]
    }
  },
  {
    axis: 1,
    confidence: 0.68,
    chart_score: 0.72,
    rehearsal_score: 0.65,
    reason: "頻出数字候補",
    score: 890,
    source: 'A1', // 欠番補足あり、中心0配置なし
    candidates: {
      box: [
        { number: "178", score: 923, probability: 0.221, reason: "リハーサル相関性高", source: 'A1' },
        { number: "124", score: 911, probability: 0.194, reason: "頻出数字候補", source: 'A1' },
        { number: "139", score: 896, probability: 0.187, reason: "統計的特徴良好", source: 'A1' },
        { number: "016", score: 884, probability: 0.179, reason: "0ありパターン", source: 'B1' },
      ],
      straight: [
        { number: "178", score: 923, probability: 0.183, reason: "リハーサル相関性高", source: 'A1' },
        { number: "124", score: 911, probability: 0.157, reason: "頻出数字候補", source: 'A1' },
        { number: "139", score: 896, probability: 0.148, reason: "統計的特徴良好", source: 'A1' },
        { number: "016", score: 884, probability: 0.142, reason: "0ありパターン", source: 'B1' },
      ]
    }
  },
  {
    axis: 8,
    confidence: 0.61,
    chart_score: 0.64,
    rehearsal_score: 0.59,
    reason: "補完パターン",
    score: 875,
    source: 'B1', // 欠番補足なし（0も含めて、すべて欠番補足しない）、中心0配置なし
    candidates: {
      box: [
        { number: "089", score: 898, probability: 0.231, reason: "パターンB最適化パターン", source: 'B1' },
        { number: "789", score: 886, probability: 0.198, reason: "統計的特徴良好", source: 'A1' },
        { number: "368", score: 873, probability: 0.185, reason: "補完パターン", source: 'A1' },
        { number: "048", score: 861, probability: 0.174, reason: "0あり特化", source: 'B1' },
      ],
      straight: [
        { number: "089", score: 898, probability: 0.192, reason: "パターンB特有の配置パターン", source: 'B1' },
        { number: "789", score: 886, probability: 0.165, reason: "統計的特徴良好", source: 'A1' },
        { number: "368", score: 873, probability: 0.154, reason: "補完パターン", source: 'A1' },
        { number: "048", score: 861, probability: 0.146, reason: "0あり特化", source: 'B1' },
      ]
    }
  }
];

// N4用の軸候補データ
export const sampleAxisCandidatesN4: AxisCandidate[] = [
  {
    axis: 7,
    confidence: 0.92,
    chart_score: 0.88,
    rehearsal_score: 0.94,
    reason: "過去L字パターン類似度94%",
    score: 985,
        source: 'A1',
    candidates: {
      box: [
        { number: "1472", score: 976, probability: 0.221, reason: "L字配置完全一致", source: 'A1' },
        { number: "0792", score: 958, probability: 0.194, reason: "過去類似パターン", source: 'B1' },
        { number: "2785", score: 941, probability: 0.176, reason: "リハーサル相関性高", source: 'A1' },
        { number: "3571", score: 927, probability: 0.168, reason: "統計的特徴良好", source: 'A1' },
        { number: "6703", score: 912, probability: 0.159, reason: "出現周期パターン", source: 'B1' },
      ],
      straight: [
        { number: "7245", score: 976, probability: 0.183, reason: "過去類似パターン6645回と94%一致", source: 'A1' },
        { number: "2790", score: 958, probability: 0.157, reason: "リハーサル相関性高", source: 'B1' },
        { number: "2785", score: 941, probability: 0.141, reason: "L字配置完全一致", source: 'A1' },
        { number: "3571", score: 927, probability: 0.135, reason: "統計的特徴良好", source: 'A1' },
        { number: "6703", score: 912, probability: 0.129, reason: "出現周期パターン", source: 'B1' },
      ]
    }
  },
  {
    axis: 2,
    confidence: 0.87,
    chart_score: 0.82,
    rehearsal_score: 0.90,
    reason: "リハーサル相関性高",
    score: 952,
        source: 'B1',
    candidates: {
      box: [
        { number: "2457", score: 971, probability: 0.231, reason: "パターンB最適化パターン", source: 'B1' },
        { number: "2783", score: 954, probability: 0.198, reason: "頻出数字候補", source: 'A1' },
        { number: "1247", score: 937, probability: 0.183, reason: "統計的特徴良好", source: 'A1' },
        { number: "0264", score: 920, probability: 0.174, reason: "0ありパターン特化", source: 'B1' },
        { number: "2348", score: 904, probability: 0.165, reason: "連番パターン", source: 'A1' },
      ],
      straight: [
        { number: "2457", score: 971, probability: 0.192, reason: "パターンB特有の配置パターン", source: 'B1' },
        { number: "2783", score: 954, probability: 0.165, reason: "中心0配置との相関性", source: 'A1' },
        { number: "1247", score: 937, probability: 0.148, reason: "統計的特徴良好", source: 'A1' },
        { number: "0264", score: 920, probability: 0.141, reason: "0ありパターン特化", source: 'B1' },
        { number: "2348", score: 904, probability: 0.136, reason: "連番パターン", source: 'A1' },
      ]
    }
  },
  {
    axis: 4,
    confidence: 0.79,
    chart_score: 0.75,
    rehearsal_score: 0.82,
    reason: "出現周期パターン",
    score: 952,
        source: 'B1',
    candidates: {
      box: [
        { number: "0457", score: 962, probability: 0.228, reason: "パターンB最適化パターン", source: 'B1' },
        { number: "2457", score: 949, probability: 0.198, reason: "頻出数字候補", source: 'A1' },
        { number: "1469", score: 933, probability: 0.189, reason: "統計的特徴良好", source: 'A1' },
        { number: "0478", score: 918, probability: 0.181, reason: "0あり特化", source: 'B1' },
      ],
      straight: [
        { number: "0457", score: 962, probability: 0.189, reason: "パターンB特有の配置パターン", source: 'B1' },
        { number: "2457", score: 949, probability: 0.162, reason: "統計的特徴良好", source: 'A1' },
        { number: "1469", score: 933, probability: 0.157, reason: "統計的特徴良好", source: 'A1' },
        { number: "0478", score: 918, probability: 0.151, reason: "0あり特化", source: 'B1' },
      ]
    }
  },
  {
    axis: 9,
    confidence: 0.68,
    chart_score: 0.72,
    rehearsal_score: 0.65,
    reason: "頻出数字候補",
    score: 918,
        source: 'A1',
    candidates: {
      box: [
        { number: "1789", score: 936, probability: 0.221, reason: "リハーサル相関性高", source: 'A1' },
        { number: "1294", score: 924, probability: 0.194, reason: "頻出数字候補", source: 'A1' },
        { number: "3496", score: 910, probability: 0.187, reason: "統計的特徴良好", source: 'A1' },
        { number: "0792", score: 897, probability: 0.179, reason: "0ありパターン", source: 'B1' },
      ],
      straight: [
        { number: "1789", score: 936, probability: 0.183, reason: "リハーサル相関性高", source: 'A1' },
        { number: "1294", score: 924, probability: 0.157, reason: "頻出数字候補", source: 'A1' },
        { number: "3496", score: 910, probability: 0.151, reason: "統計的特徴良好", source: 'A1' },
        { number: "0792", score: 897, probability: 0.145, reason: "0ありパターン", source: 'B1' },
      ]
    }
  }
];

// サンプル最終予測結果（全パターン対応）
export const sampleFinalPredictions = {
  // ナンバーズ3 パターンA
  n3_a: {
    straight: [
      {
        number: "253",
        probability: 0.183,
        reason: "過去類似パターンと94%一致"
      },
      {
        number: "178",
        probability: 0.157,
        reason: "リハーサル相関性高"
      },
      {
        number: "915",
        probability: 0.141,
        reason: "L字配置完全一致"
      }
    ],
    box: [
      {
        number: "235",
        probability: 0.221,
        reason: "過去類似パターン"
      },
      {
        number: "178",
        probability: 0.194,
        reason: "統計的特徴良好"
      },
      {
        number: "159",
        probability: 0.176,
        reason: "頻出数字候補"
      }
    ]
  },
  // ナンバーズ3 パターンB
  n3_b: {
    straight: [
      {
        number: "301",
        probability: 0.192,
        reason: "パターンB特有の配置パターン"
      },
      {
        number: "678",
        probability: 0.165,
        reason: "中心0配置との相関性"
      },
      {
        number: "945",
        probability: 0.148,
        reason: "統計的特徴良好"
      }
    ],
    box: [
      {
        number: "013",
        probability: 0.231,
        reason: "パターンB最適化パターン"
      },
      {
        number: "678",
        probability: 0.201,
        reason: "過去類似パターン"
      },
      {
        number: "459",
        probability: 0.182,
        reason: "頻出数字候補"
      }
    ]
  },
  // ナンバーズ4 パターンA
  n4_a: {
    straight: [
      {
        number: "7245",
        probability: 0.183,
        reason: "過去類似パターン6645回と94%一致"
      },
      {
        number: "2783",
        probability: 0.157,
        reason: "リハーサル相関性高"
      },
      {
        number: "7208",
        probability: 0.141,
        reason: "L字配置完全一致"
      },
      {
        number: "2751",
        probability: 0.128,
        reason: "統計的特徴良好"
      }
    ],
    box: [
      {
        number: "2457",
        probability: 0.221,
        reason: "L字配置完全一致"
      },
      {
        number: "0278",
        probability: 0.194,
        reason: "過去類似パターン"
      },
      {
        number: "1247",
        probability: 0.176,
        reason: "リハーサル相関性高"
      }
    ]
  },
  // ナンバーズ4 パターンB
  n4_b: {
    straight: [
      {
        number: "8036",
        probability: 0.189,
        reason: "パターンB特有の配置パターン"
      },
      {
        number: "4592",
        probability: 0.162,
        reason: "中心0配置との相関性"
      },
      {
        number: "7164",
        probability: 0.145,
        reason: "統計的特徴良好"
      },
      {
        number: "2937",
        probability: 0.132,
        reason: "過去類似パターン"
      }
    ],
    box: [
      {
        number: "0368",
        probability: 0.228,
        reason: "パターンB最適化パターン"
      },
      {
        number: "4592",
        probability: 0.198,
        reason: "頻出数字候補"
      },
      {
        number: "7164",
        probability: 0.183,
        reason: "統計的特徴良好"
      }
    ]
  }
};

// サンプル統計データ
export const sampleStatisticsData: StatisticsData = {
  period: "30d",
  metrics: {
    overall_accuracy: 0.583,
    straight_accuracy: 0.387,
    box_accuracy: 0.581,
    axis_accuracy: 0.724,
    total_predictions: 30,
    hits: {
      straight: 11,
      box: 17,
      axis: 22
    }
  },
  axis_breakdown: [
    {
      axis: 7,
      accuracy: 0.72,
      total_used: 25,
      hits: 18
    },
    {
      axis: 2,
      accuracy: 0.68,
      total_used: 22,
      hits: 15
    },
    {
      axis: 5,
      accuracy: 0.61,
      total_used: 18,
      hits: 11
    },
    {
      axis: 1,
      accuracy: 0.59,
      total_used: 17,
      hits: 10
    },
    {
      axis: 8,
      accuracy: 0.54,
      total_used: 13,
      hits: 7
    },
    {
      axis: 3,
      accuracy: 0.52,
      total_used: 17,
      hits: 9
    }
  ],
  trend_data: [
    { date: "2025-10-01", accuracy: 0.55 },
    { date: "2025-10-02", accuracy: 0.58 },
    { date: "2025-10-03", accuracy: 0.52 },
    { date: "2025-10-04", accuracy: 0.61 },
    { date: "2025-10-05", accuracy: 0.59 },
    { date: "2025-10-06", accuracy: 0.63 },
    { date: "2025-10-07", accuracy: 0.57 },
    { date: "2025-10-08", accuracy: 0.60 }
  ]
};

// サンプル履歴データ
export const sampleHistoryData: HistoryItem[] = [
  {
    id: 1,
    round: 6700,
    date: "2025-10-07",
    numbers_type: "N3",
    selected_axes: [5],
    predicted_number: "253",
    prediction_type: "box",
    actual_winning: "253",
    is_hit: true,
    confidence: 0.912,
    predicted_at: "2025-10-07T17:30:00Z"
  },
  {
    id: 2,
    round: 6699,
    date: "2025-10-06",
    numbers_type: "N4",
    selected_axes: [7, 2],
    predicted_number: "7245",
    prediction_type: "straight",
    actual_winning: "8945",
    is_hit: false,
    confidence: 0.875,
    predicted_at: "2025-10-06T17:25:00Z"
  },
  {
    id: 3,
    round: 6698,
    date: "2025-10-05",
    numbers_type: "N3",
    selected_axes: [1],
    predicted_number: "178",
    prediction_type: "box",
    actual_winning: "178",
    is_hit: true,
    confidence: 0.889,
    predicted_at: "2025-10-05T17:20:00Z"
  },
  {
    id: 4,
    round: 6697,
    date: "2025-10-04",
    numbers_type: "N4",
    selected_axes: [3, 8],
    predicted_number: "3847",
    prediction_type: "straight",
    actual_winning: "2193",
    is_hit: false,
    confidence: 0.823,
    predicted_at: "2025-10-04T17:15:00Z"
  },
  {
    id: 5,
    round: 6696,
    date: "2025-10-03",
    numbers_type: "N3",
    selected_axes: [9],
    predicted_number: "915",
    prediction_type: "box",
    actual_winning: "915",
    is_hit: true,
    confidence: 0.945,
    predicted_at: "2025-10-03T17:10:00Z"
  }
];

// 予測タイプ別の実績データ
export const samplePredictionTypeStats = [
  { name: "N3 ストレート", value: 45.2, fill: "#ef4444" },
  { name: "N3 ボックス", value: 63.8, fill: "#10b981" },
  { name: "N4 ストレート", value: 38.7, fill: "#f59e0b" },
  { name: "N4 ボックス", value: 58.1, fill: "#3b82f6" }
];

