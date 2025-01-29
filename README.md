# FPL Points Prediction Project

A machine learning system that predicts Fantasy Premier League (FPL) points using neural networks and exponential moving averages. View predictions at my [website](https://bacunamateta.pythonanywhere.com/ai_team
).
## Features

- **Points Prediction**: Neural network model trained on historical FPL data.
- **Moving Averages**: 6-gameweek EWMA for both team and player performance.
- **Live Predictions**: Interactive table showing predicted points for upcoming gameweeks.
- **Transfer Optimization**: Algorithm to suggest optimal transfers.

## Technical Stack

- **Data Processing**: Python, Pandas
- **Machine Learning**: TensorFlow Neural Network
- **Data Source**: FPL API
- **Feature Engineering**:
  - Player performance metrics
  - Team form indicators
  - 6-week exponential moving averages

## Repository Structure

```bash
├── fetch_fpl_data.py      # FPL API data fetching
├── time_series.py         # Moving average calculations
├── ml_pipeline.py         # Neural network implementation
├── main.py                # Main execution script
├── transfer_algorithm.py  # Transfer suggester
└── optimization.py        # Team optimization
```

## Live Demo

Visit the [website](https://bacunamateta.pythonanywhere.com/ai_team) to see:
- Predicted points for all players
- Transfer recommendation tool

## Future Development

- Real-time data integration
- Enhanced prediction accuracy
- Advanced visualization features
