from enum import Enum
from typing import Optional
from pydantic import BaseModel
from typing import Union, Literal

from models import Model, openai_client, anthropic_client
from messages import Messages
model = Model(openai_client, 'gpt-4o-mini')

class Function(BaseModel):
    type: Literal["function"]
    name: str
    start_line_number: int
    end_line_number: int
    first_line_text: str
    summary: str
    docstring: Optional[str]
    subsections: list['Function']


class Class(BaseModel):
    type: Literal["class"]
    name: str
    start_line_number: int
    end_line_number: int
    first_line_text: st
    summary: str
    docstring: Optional[str]

    methods:list[Function]
    fields:list[str]


class OtherSection(BaseModel):
    type: Literal["other_section"]
    name: str
    start_line_number: int
    end_line_number: int
    summary: str

    subsections: list['Section']

Section = Union[Class, Function, OtherSection]

class _FileSummary(BaseModel):
    summary: str
    sections: list[Section]

system_message = "You are a helpful assistant."
instruction = """Summarize the following file. Don't say anything about implicitly defined variables/classes/functions. Use docstring for any comments at the start of a function/method/class definition that is used like a docstring (e.g. describes the code). Use type=other_section for:
* files that aren't code (e.g., text, latex, markdown).
* to split up very long code files into logical sections.
* to split up very long functions/methods into logical sections.
* for code that isn't part of a function/class definition.  e.g. in a shell script, or the imports.
The code is:

"""

previous_summary_instruction = """
Here is a summary written for the previous version of the file.  You may need to update the line numbers.  You should just copy descriptions etc. if the summaries if the previous version of the file is still accurate.  If the file has changed so much that the previous summary isn't accurate, then you should change it.

The previous summary is:

"""

class ProjectSummary():
    def __init__(self, file_summaries):
        assert isinstance(file_summaries, dict)
        self.file_summaries = file_summaries #Dict mapping file_path to FileSummary

    def update(self, updated_files):
        assert isinstance(updated_files, list)

        result = {**self.file_summaries}
        for path in updated_files:
            if path in self.file_summaries:
                _file_summary = self.file_summaries[path].update(path)
            else:
                _file_summary = file_summary(path)
            result[path] = _file_summary
        return ProjectSummary(result)

    def update_write(self, content):
        raise NotImplementedError()

    def dump(self):
        return {path: fs.dump() for path, fs in self.file_summaries.items()}

def project_summary(tracked_file_list):
    project_summary = ProjectSummary({})
    return project_summary.update(tracked_file_list)

class FileSummary():
    """
    A summary of a file.  
    summary: high-level summary
    subsections: more detailed summaries of parts of the file.  Implemented as dict mapping section title (str) to SectionSummary.
    """
    def __init__(self, summary, subsections):
        assert isinstance(summary, str)
        assert isinstance(subsections, dict) 

        self.summary = summary
        self.subsections = subsections

    def update(self, path, previous_summary=None):
        with open(path, 'r') as file:
            lines = file.readlines()

        lines_with_nums = []
        for i in range(len(lines)):
            lines_with_nums.append(f'{i}:{lines[i]}')

        file_with_line_nos = '\n'.join(lines_with_nums)
        prompt = instruction + file_with_line_nos
        if previous_summary:
            prompt = prompt + previous_summary_instruction + previous_summary

        messages = Messages([])
        messages = messages.append_text('user', prompt)
        response = model.response_text(system_message, messages, False, response_format=_FileSummary)
        print(response)

        subsections = {}
#        for start_line, end_line, section_title, summary in re.findall(pattern, response, re.MULTILINE):
#            subsections[section_title] = SectionSummary(int(start_line), int(end_line), summary, {})
        return FileSummary("", subsections)

    def dump(self):
        subsections_dump = {title: ss.dump() for title, ss in self.subsections.items()}
        return {'summary': self.summary, 'subsections': subsections_dump}

def file_summary(path):
    file_summary = FileSummary("", {})
    return file_summary.update(path)

class SectionSummary():
    def __init__(self, start_line, end_line, summary, subsections):
        assert isinstance(start_line, int)
        assert isinstance(end_line, int)
        assert isinstance(summary, str)
        assert isinstance(subsections, dict)

        self.start_line = start_line
        self.end_line = end_line
        self.summary = summary
        self.subsections = subsections

    def dump(self):
        return {'start_line' : self.start_line, 'end_line' : self.end_line, 'summary': self.summary, 'subsections': self.subsections}
