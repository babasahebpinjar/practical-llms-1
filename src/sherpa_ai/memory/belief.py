from typing import Callable, List

from sherpa_ai.actions.base import BaseAction
from sherpa_ai.events import Event, EventType


class Belief:
    def __init__(self):
        # TODO: Handle long belief history, if it's longer than the context size
        # maybe use summarization or a vector db

        self.events: List[Event] = []
        self.internal_events: List[Event] = []
        self.current_task: Event = None

    def update(self, observation: Event):
        if observation in self.events:
            return

        self.events.append(observation)

    def update_internal(
        self,
        event_type: EventType,
        agent: str,
        content: str,
    ):
        event = Event(event_type=event_type, agent=agent, content=content)
        self.internal_events.append(event)

    def get_by_type(self, event_type):
        return [
            event for event in self.internal_events if event.event_type == event_type
        ]

    def set_current_task(self, task: Event):
        self.current_task = task

    def get_context(self, token_counter: Callable[[str], int], max_tokens=4000):
        """
        Get the context of the agent

        Args:
            token_counter: Token counter
            max_tokens: Maximum number of tokens

        Returns:
            str: Context of the agent
        """
        context = ""
        for event in reversed(self.events):
            if (
                event.event_type == EventType.task
                or event.event_type == EventType.result
            ):
                context = event.content + "\n" + context

                if token_counter(context) > max_tokens:
                    break

        if context == "":
            exit(1)

        return context

    def get_internal_history(
        self, token_counter: Callable[[str], int], max_tokens=4000
    ):
        """
        Get the internal history of the agent

        Args:
            token_counter: Token counter
            max_tokens: Maximum number of tokens

        Returns:
            str: Internal history of the agent
        """
        results = []
        current_tokens = 0

        for event in reversed(self.internal_events):
            results.append(event.content)
            current_tokens += token_counter(event.content)

            if current_tokens > max_tokens:
                break

        context = "\n".join(reversed(results))

        return context

    def get_histories_excluding_types(
        self,
        token_counter: Callable[[str], int],
        exclude_type: [EventType],
        max_tokens=4000,
    ):
        """
        Get the internal history of the agent with out events in the excluded_type

        Args:
            token_counter: Token counter
            max_tokens: Maximum number of tokens
            exclude_type: List of events to be excluded

        Returns:
            str: Internal history of the agent
        """
        results = []
        feedback = []
        current_tokens = 0
        for event in reversed(self.internal_events):
            if event.event_type not in exclude_type:
                if event.event_type == EventType.feedback:
                    feedback.append(event.content)
                else:
                    results.append(event.content)
            current_tokens += token_counter(event.content)
            if current_tokens > max_tokens:
                break
        context = "\n".join(set(reversed(results))) + "\n".join(set(feedback))
        return context

    def set_actions(self, actions: List[BaseAction]):
        self.actions = actions

    @property
    def action_description(self):
        return "\n".join([str(action) for action in self.actions])

    def get_action(self, action_name) -> BaseAction:
        result = None
        for action in self.actions:
            if action.name == action_name:
                result = action
                break

        return result

    @property
    def __dict__(self):
        return {
            "events": [event.__dict__ for event in self.events],
            "internal_events": [event.__dict__ for event in self.internal_events],
            "current_task": self.current_task.__dict__ if self.current_task else None,
        }

    @classmethod
    def from_dict(cls, data):
        belief = cls()
        belief.events = [Event.from_dict(event) for event in data["events"]]
        belief.internal_events = [
            Event.from_dict(event) for event in data["internal_events"]
        ]
        belief.current_task = (
            Event.from_dict(data["current_task"]) if data["current_task"] else None
        )
        return belief
