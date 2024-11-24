import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from src.prompts import Prompts


class LlmDndGuessingGame:
    """Main Clas for running the LLM driven D&D Guessing Game."""
    def __init__(self) -> None:
        """Init LlmDndGuessingGame class."""
        load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.messages = []
        self.total_score = 0
        self.prompts = Prompts()
        self.option_scores = {}

    def start_game(self, character_class: str) -> str:
        """Starts the game via streamlit interface with the initial dungeon master instruction prompt.

        Args:
            character_class (str): D&D class chosen by the user via streamlit interface.

        Returns:
            assistant_message_cleaned (str): LLM response with removed game scores.
        """
        # setup prompt
        self.messages = [
            {"role": "system",
             "content": self.prompts.dungeon_master_instructions_v1
                        + f"\n User has chosen character class: {character_class}"}
        ]
        # client call
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            max_tokens=500,
            temperature=0.7,
        )
        assistant_message = response.choices[0].message.content

        # removes scores from response; adds cleaned msg to LLM context
        assistant_message_cleaned = self.extract_and_remove_scores(assistant_message)
        self.messages.append({"role": "assistant", "content": assistant_message_cleaned})
        return assistant_message_cleaned

    def evaluate_choice(self, current_scenario: str, user_choice: str, character_class: str) -> str:
        """Continuation function for evaluating the user's input to the generated scenario while generating the
           new scenario with the evaluation prompt.

        Args:
            current_scenario (str): Current scenario to evaluate.
            user_choice (str): Choice in terms of option the user took.
            character_class (str): User chosen D&D class (via streamlit dropdown menu).

        Returns:
            assistant_message_cleaned (str): LLM response with removed game scores.
        """
        # adds scenario and user choice to LLM context
        self.messages.append({"role": "assistant", "content": current_scenario})
        self.messages.append({"role": "user", "content": user_choice})

        # setup prompt
        self.messages.append(
            {"role": "system", "content": self.prompts.evaluation_instructions_v1 +
                                          f"\n User has chosen character class: {character_class}"}
        )

        # client call
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.messages,
            max_tokens=500,
            temperature=0.7,
        )
        assistant_message = response.choices[0].message.content

        # extracts score for evaluation from response
        points = self.extract_points_from_evaluation(assistant_message)
        self.total_score += points

        # removes scores from response (since it includes new generated scenario); adds cleaned msg to LLM context
        assistant_message_cleaned = self.extract_and_remove_scores(assistant_message)
        self.messages.append({"role": "assistant", "content": assistant_message_cleaned})
        return assistant_message_cleaned

    @staticmethod
    def extract_current_scenario(evaluation_response: str) -> str:
        """Extracts the latest scenario and options from the evaluation response.

        Args:
            evaluation_response (str): The assistant's evaluation response containing the new scenario and options.

        Returns:
            (str): The extracted scenario and options to be used as the current scenario.
        """
        # regex pattern for option
        pattern = r"^(?:.*?\n)?(As .+?)(Options:\nOption 1:.*?Option 4:.*?)(?:Please choose an option.*|$)"
        match = re.search(pattern, evaluation_response, re.DOTALL)
        if match:
            current_scenario = match.group(1) + match.group(2)
            return current_scenario.strip()
        else:
            # in case LLM hallucinates and pattern is not found, returns entire response
            return evaluation_response.strip()

    def extract_and_remove_scores(self, message: str) -> str:
        """Extracts the hidden scores from the options and removes them from the message.

        Args:
            message (str): The assistant's message containing options with hidden scores.

        Returns:
            message_cleaned (str): The message with scores removed.
        """
        # regex pattern for score
        pattern = r'(Option \d+: .*?) <<Score:([+-]?\d+\.?\d*)>>'
        options_with_scores = re.findall(pattern, message, re.DOTALL)

        # removes scores from message
        message_cleaned = re.sub(r' <<Score:[+-]?\d+\.?\d*>>', '', message)

        # stores option scores
        self.option_scores = {}
        for option_text, score in options_with_scores:
            # gets option number
            option_number_match = re.search(r'Option (\d+):', option_text)
            if option_number_match:
                option_number = option_number_match.group(1)
                self.option_scores[option_number] = float(score)
            else:
                # in case LLM hallucinates and option number is not given
                # -- !!case it not handled yet!! --
                continue

        return message_cleaned

    def extract_points_from_evaluation(self, message: str) -> float:
        """Extracts the points awarded or deducted from the assistant's evaluation message.

        Args:
            message (str): The assistant's evaluation message.

        Returns:
            (float): The points awarded or deducted.
        """
        # regex pattern for score (on LLM response to user input)
        match = re.search(r'You (gained|lost) ([+-]?\d+\.?\d*) points?', message)
        if match:
            points = float(match.group(2))
            if match.group(1) == 'lost':
                points = -points        # *(-1) if negative
            return points
        else:
            # if LLM hallucinates and misses to explicitly tell the score, looks up the last user input to determine
            # option taken and corresponding score
            last_user_choice = self.messages[-2]['content']
            option_number_match = re.search(r'Option (\d+)', last_user_choice)
            if option_number_match:
                option_number = option_number_match.group(1)
                points = self.option_scores.get(option_number, 0.0)
                return points
            else:
                return 0.0

    def get_hint(self, current_scenario: str, player_class: str) -> str:
        """Generate a hint based on the current scenario and the player's class.

        Args:
            current_scenario (str): The current scenario description.
            player_class (str): User chosen D&D class (via streamlit dropdown menu).

        Returns:
            hint (str): The hint message.
        """
        # adds scenario to LLM context
        self.messages.append({"role": "assistant", "content": current_scenario})

        # setup prompt
        self.messages.append(
            {"role": "system",
             "content": f"The user is playing as a {player_class}. Provide a subtle hint for the current scenario."}
        )

        # client call
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=self.messages,
            max_tokens=100,
            temperature=0.7,
        )
        hint = response.choices[0].message.content

        # adds hint to LLM context
        self.messages.append({"role": "assistant", "content": hint})
        return hint
