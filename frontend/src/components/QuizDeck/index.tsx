import { useEffect, useState } from "react";
import "./styles.scss";
import { Button, Modal } from "antd";
import http from "utils/api"; // Assuming `http` is the instance for API requests
import { useParams } from "react-router";

interface QuizProps {
  cards: { front: string; back: string; hint: string }[];
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
      recordWrongAnswer(currentCard);
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
          console.log("inside")
          await http.post(`/deck/${id}/update-leaderboard`, {
            userId: localId,
            userEmail: email,
            correct: finalScore, // Pass the calculated final score
            incorrect: finalIncorrectAnswers, // Pass the calculated final incorrect answers
          });
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
  };

  if (isQuizFinished) {
    return (
      <div className="quiz-summary">
        <h2>Quiz Complete!</h2>
        <p>Your Score: {score} / {cards.length}</p>
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
