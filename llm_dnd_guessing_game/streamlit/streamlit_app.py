import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from src.run import LlmDndGuessingGame


def format_response(response: str) -> str:
    """Ensures each option starts on a new line (includes two spaces before line breaks due to streamlit chat interface
       'bug').

    Args:
        response (str): The original response from the assistant.

    Returns:
        (str): The formatted response or the original response if no "Options" is found.
    """
    if "Options:" in response:
        parts = response.split("Options:")
        scenario_text = parts[0].strip()
        options_text = parts[1].strip()
        options = [
            f"{line.strip()}  " for line in options_text.split("\n") if line.strip().startswith("Option")
        ]
        formatted_options = "\n".join(options)
        return f"{scenario_text}\n\n**Options:**\n\n{formatted_options}"
    return response


def main() -> None:
    st.title("D&D Adventure: LLM-Powered Dungeon Master")

    # init session states
    if "game_started" not in st.session_state:
        st.session_state.game_started = False

    if "game_stats" not in st.session_state:
        st.session_state.game_stats = {
            "games_played": 0,
            "guesses_per_game": [],
        }

    # ----------------- SIDEBAR ---------------------
    with st.sidebar:
        st.header("Game Settings")
        dnd_classes = [
            "Warlock",
            "Wizard",
            "Fighter",
            "Rogue",
            "Cleric",
            "Ranger",
            "Paladin",
            "Barbarian",
            "Bard",
            "Monk",
        ]
        if "player_class" not in st.session_state:
            st.session_state.player_class = dnd_classes[0]
        st.session_state.player_class = st.selectbox("Select a D&D class:", dnd_classes)
        st.write(f"🎲 You selected: **{st.session_state.player_class}**")

        # start Game Button
        if not st.session_state.game_started:
            if st.button("Start Game"):
                st.session_state.game_started = True
                st.session_state.game = LlmDndGuessingGame()
                st.session_state.current_scenario = st.session_state.game.start_game(st.session_state.player_class)
                current_scenario_formatted = format_response(st.session_state.current_scenario)
                st.session_state.messages = []
                st.session_state.messages.append(
                    {"role": "assistant", "content": current_scenario_formatted}
                )
                st.session_state.total_score = 0.0
                st.session_state.scenario_count = 0
                st.session_state.hints_used = 0
                st.session_state.guesses_in_current_game = 0

        st.header("Game Rules")
        st.markdown(
            """
            Welcome to the D&D Adventure Simulator! Here's how it works:

            - **Objective**: Make decisions to progress through the adventure based on your character's class and the scenario presented.
            - **Options**: Each scenario presents four options:
                - **+1 Point**: The most logical and effective choice.
                - **+0.5 Points**: A creative choice that could work.
                - **0 Points**: A neutral or ineffective choice.
                - **-0.5 Points**: A counterproductive or foolish choice.
            - **Hints**: You can request a hint for subtle guidance, but each hint costs **-0.25 points**.
            - Use your reasoning and your character's unique abilities to make the best decision!
            """
        )

    # ----------------- MAIN ---------------------
    if st.session_state.get("game_started", False):
        tab1, tab2, tab3 = st.tabs(["Play", "Scoreboard", "Stats"])

        # ----------------- PLAY TAB ---------------------
        with tab1:
            chat_container = st.container()
            user_input = st.chat_input("Enter your choice (e.g., Option 1, Option 2):")

            if "messages" not in st.session_state:
                st.session_state.messages = []

            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                st.session_state.guesses_in_current_game += 1

                # evaluates user input and creates new scenario
                evaluation = st.session_state.game.evaluate_choice(
                    st.session_state.current_scenario, user_input, st.session_state.player_class
                )

                formatted_evaluation = format_response(evaluation)
                st.session_state.messages.append(
                    {"role": "assistant", "content": formatted_evaluation}
                )

                st.session_state.total_score = st.session_state.game.total_score
                st.session_state.scenario_count += 1

                st.session_state.current_scenario = st.session_state.game.extract_current_scenario(
                    evaluation
                )

            # display chat history
            with chat_container:
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"], unsafe_allow_html=True)

                # hint button
                if st.button("Get Hint"):
                    hint = st.session_state.game.get_hint(
                        st.session_state.current_scenario, st.session_state.player_class
                    )
                    st.session_state.messages.append({"role": "assistant", "content": f"**Hint:** {hint}"})
                    st.session_state.hints_used += 1
                    st.session_state.total_score -= 0.25
                    st.rerun()  # refresh to display hint immediately

                # auto-scroll to latest message
                st.write(
                    "<script>window.scrollTo(0, document.body.scrollHeight);</script>",
                    unsafe_allow_html=True,
                )

        # ----------------- SCOREBOARD TAB ---------------------
        with tab2:
            st.header("Scoreboard")
            st.write(f"**Player Class:** {st.session_state.player_class}")
            st.write(f"**Total Score:** {st.session_state.total_score}")
            st.write(f"**Scenarios Played:** {st.session_state.scenario_count}")
            st.write(f"**Hints Used:** {st.session_state.hints_used}")

            if st.button("New Game"):
                st.session_state.game_stats["games_played"] += 1
                st.session_state.game_stats["guesses_per_game"].append(st.session_state.guesses_in_current_game)

                # resets the game state
                st.session_state.game_started = False
                st.session_state.game = None
                st.session_state.current_scenario = None
                st.session_state.messages = []
                st.session_state.total_score = 0.0
                st.session_state.scenario_count = 0
                st.session_state.hints_used = 0
                st.session_state.guesses_in_current_game = 0

        # ----------------- STATS TAB ---------------------
        with tab3:
            st.header("Stats")
            st.write(f"**Games Played:** {st.session_state.game_stats['games_played']}")
            if st.session_state.game_stats["games_played"] > 0:
                average_guesses = sum(st.session_state.game_stats["guesses_per_game"]) / st.session_state.game_stats[
                    "games_played"]
                st.write(f"**Average Score per Game:** {average_guesses:.2f}")
            else:
                st.write("No games played yet.")

            # bar chart
            if st.session_state.game_stats["games_played"] > 0:
                st.bar_chart(pd.DataFrame({
                    "Game Number": list(range(1, st.session_state.game_stats["games_played"] + 1)),
                    "Guesses": st.session_state.game_stats["guesses_per_game"]
                }).set_index("Game Number"))


if __name__ == "__main__":
    main()
