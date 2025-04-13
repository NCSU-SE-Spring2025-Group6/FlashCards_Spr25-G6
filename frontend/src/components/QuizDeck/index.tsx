import { useEffect, useState } from "react";
import "./styles.scss";
import { Button, Modal, message } from "antd";
import http from "utils/api"; // Assuming `http` is the instance for API requests
import { useParams } from "react-router";

interface QuizProps {
  cards: { front: string; back: string; hint: string }[];
}

interface GamificationData {
  streak?: {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string;
  };
  achievements_earned?: any[];
  xp_earned?: number;
  level_up?: boolean;
  new_level?: number;
}

export default function Quiz({ cards }: QuizProps) {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isQuizFinished, setIsQuizFinished] = useState(false);
  const [shuffledOptions, setShuffledOptions] = useState<string[]>([]);
  const [incorrectAnswers, setIncorrectAnswers] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [hintUsed, setHintUsed] = useState(false);
  const [gamificationData, setGamificationData] = useState<GamificationData | null>(null);
  const { id } = useParams();
  const currentCard = cards[currentCardIndex];

  const handleHintModal = () => {
    if (!showHint) {
      setHintUsed(true);
    }
    setShowHint(!showHint);
  };

  useEffect(() => {
    if (currentCard) {
      setShuffledOptions(shuffleOptions(cards, currentCard.back));
      setShowHint(false);
      setHintUsed(false);
    }
  }, [currentCard, cards]);

  function shuffleOptions(cards: QuizProps["cards"], correctAnswer: string) {
    const otherOptions = cards
      .map((card) => card.back)
      .filter((answer) => answer !== correctAnswer);
    const shuffled = [correctAnswer, ...otherOptions.slice(0, 3)].sort(
      () => Math.random() - 0.5
    );
    return shuffled;
  }

  const recordWrongAnswer = async (card: {front: string, back: string, hint: string}) => {
    const flashCardUser = window.localStorage.getItem("flashCardUser");

    const { localId = "", email = "" } = flashCardUser ? JSON.parse(flashCardUser) : {};

    if (localId) {
      try {
        await http.post(`/deck/${id}/record-wrong-answer`, {
          userId: localId,
          front: card.front,
          back: card.back,
          hint: card.hint,
        });
        console.log("Recorded successfully")
      } catch (error) {
        console.error("Error recording wrong answer:", error);
      }
    }
  };

  const handleOptionClick = (option: string) => {
    setSelectedOption(option);
    const isCorrect = option === currentCard.back;
    let delta = 0;
    let incorrectDelta = 0;

    if (isCorrect) {
      delta = hintUsed ? 0.5 : 1; // Use hintUsed instead of showHint
      setScore((prev) => prev + delta);
    } else {
      incorrectDelta = 1;
      setIncorrectAnswers((prev) => prev + incorrectDelta);
    }

    setTimeout(() => {
      setSelectedOption(null);
      if (currentCardIndex + 1 < cards.length) {
        setCurrentCardIndex((prevIndex) => prevIndex + 1);
      } else {
        const finalScore = score + delta;
        const finalIncorrect = incorrectAnswers + incorrectDelta;
        setIsQuizFinished(true);
        updateLeaderboard(finalScore, finalIncorrect);
      }
    }, 1000);
  };
  
  // Update leaderboard function
  const updateLeaderboard = async (finalScore: number, finalIncorrectAnswers: number) => {
    const flashCardUser = window.localStorage.getItem("flashCardUser");
    const { localId = "", email = "" } = flashCardUser ? JSON.parse(flashCardUser) : {};

    if (localId && email) {
      try {
        // Fetch the user's current score for this deck
        const response = await http.get(`/deck/${id}/user-score/${localId}`);
        const existingScore = response.data?.score["correct"]; // Assuming the score is returned here
        
        // Only update if the new score is higher than the existing score
        if (finalScore > existingScore || (response.data.score["correct"] === 0 && response.data.score["incorrect"] === 0)) {
          await http.post(`/deck/${id}/update-leaderboard`, {
            userId: localId,
            userEmail: email,
            correct: finalScore, // Pass the calculated final score
            incorrect: finalIncorrectAnswers, // Pass the calculated final incorrect answers
          });
        }
        
        // Record activity for streak regardless of score
        try {
          // First record activity to update streak
          const activityResponse = await http.post(`/gamification/record-activity/${localId}`, {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
          });
          
          // Then award XP for completing the quiz
          const xpResponse = await http.post(`/gamification/award-xp/${localId}`, {
            activity_type: "complete_quiz",
            metadata: {
              score: finalScore,
              total: cards.length,
              deck_id: id
            }
          });
          
          // Get gamification data for display
          const gamificationInfo = {
            streak: activityResponse.data?.streak,
            achievements_earned: [
              ...(activityResponse.data?.achievements_earned || []),
              ...(xpResponse.data?.achievements_earned || [])
            ],
            xp_earned: xpResponse.data?.xp_earned,
            level_up: xpResponse.data?.level_up,
            new_level: xpResponse.data?.level
          };
          
          setGamificationData(gamificationInfo);
          
          // Show achievement notifications
          if (gamificationInfo.achievements_earned && gamificationInfo.achievements_earned.length > 0) {
            gamificationInfo.achievements_earned.forEach(achievement => {
              if (achievement) {
                message.success(`Achievement Unlocked: ${achievement.name}! (+${achievement.xp_awarded} XP)`);
              }
            });
          }
          
          // Show level up notification
          if (gamificationInfo.level_up) {
            message.success(`Level Up! You've reached level ${gamificationInfo.new_level}!`);
          }
          
        } catch (error) {
          console.error("Error with gamification:", error);
        }
      } catch (error) {
        console.error("Error updating leaderboard:", error);
      }
    }
  };

  const restartQuiz = () => {
    setCurrentCardIndex(0);
    setScore(0);
    setIsQuizFinished(false);
    setIncorrectAnswers(0);
    setGamificationData(null);
  };

  if (isQuizFinished) {
    return (
      <div className="quiz-summary">
        <h2>Quiz Complete!</h2>
        <p>Your Score: {score} / {cards.length}</p>
        
        {gamificationData && (
          <div className="gamification-summary">
            {gamificationData.xp_earned !== undefined && gamificationData.xp_earned > 0 && (
              <p className="xp-earned">+{gamificationData.xp_earned} XP</p>
            )}
            
            {gamificationData.streak && (
              <p className="streak-info">
                Current Streak: {gamificationData.streak.current_streak} day{gamificationData.streak.current_streak !== 1 ? 's' : ''}
              </p>
            )}
            
            {gamificationData.achievements_earned && gamificationData.achievements_earned.length > 0 && (
              <div className="achievements-earned">
                <h4>Achievements Unlocked:</h4>
                <ul>
                  {gamificationData.achievements_earned.map((achievement, index) => 
                    achievement && (
                      <li key={index}>
                        {achievement.name} - {achievement.description} 
                        <span className="achievement-xp">+{achievement.xp_awarded} XP</span>
                      </li>
                    )
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
        
        <button className="btn btn-primary" onClick={restartQuiz}>
          Restart Quiz
        </button>
      </div>
    );
  }

  return (
    <div className="quiz-container">
      <div className="quiz-question-header">
        <h2>{currentCard.front}</h2>
        {currentCard.hint && (
          <Button 
            type="link"
            onClick={handleHintModal}
            className="hint-button"
          >
            {showHint ? 'Hide Hint' : 'Show Hint'}
          </Button>
        )}
      </div>

      <Modal
        title="Hint"
        open={showHint}
        onCancel={handleHintModal}
        footer={[
          <Button key="close" onClick={handleHintModal}>
            Close
          </Button>
        ]}
        width={600}
      >
        <div className="hint-content">
          <p>{currentCard.hint}</p>
        </div>
      </Modal>
      <div className="options">
        {shuffledOptions.map((option, index) => (
          <button
            key={index}
            className={`option-btn ${
              selectedOption
              ? option === currentCard.back
              ? "highlight-correct"
              : selectedOption === option
              ? "highlight-incorrect"
              : ""
              : ""
              }`}
            onClick={() => handleOptionClick(option)}
            disabled={!!selectedOption}
          >
            {option}
          </button>
        ))}
      </div>
      <p>Score: {score}</p>
      <p>
        Question {currentCardIndex + 1} / {cards.length}
      </p>
    </div>
  );
}
