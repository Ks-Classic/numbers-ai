export interface StatisticsData {
  period: string;
  metrics: {
    overall_accuracy: number;
    straight_accuracy: number;
    box_accuracy: number;
    axis_accuracy: number;
    total_predictions: number;
    hits: {
      straight: number;
      box: number;
      axis: number;
    };
  };
  axis_breakdown: {
    axis: number;
    accuracy: number;
    total_used: number;
    hits: number;
  }[];
  trend_data: {
    date: string;
    accuracy: number;
  }[];
}

export interface ChartDataPoint {
  name: string;
  value: number;
  fill?: string;
}

