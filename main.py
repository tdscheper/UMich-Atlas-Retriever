import io
import os
import sys
import time
import stat
from enum import Enum
from getpass import getpass
from heapq import heappop, heappush
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from specialprint import horizontal_align_print


# Change any of these if you want
# If you don't, you'll need to type them in each time
UNIQNAME    = ''
PASSWORD    = ''
FILE_PATH   = ''
SORT_METHOD =  0  # Must be integer 1-5. Refer to class on line 74


# If you're on Mac you shouldn't have to change this
CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


ENCODING = 'utf-8'
ELEMENTS = {
    'title'       : '/html/body/div[1]/div[1]/div/div[1]/div/div[1]/h2',
    'grade'       : '/html/body/div[1]/div[1]/div/div[2]/div/p[1]/span',
    'workload'    : '/html/body/div[1]/div[4]/div[2]/div[3]/div[1]/h5',
    'uniqname'    : "//input[@id='login']",
    'password'    : "//input[@id='password']",
    'login_submit': "//input[@id='loginSubmit']"
}
DISPLAY_LENGTHS = {
    'name'    : 12,  # Longest name is 12 characters. Ex: ASIANPAM 214
    'title'   : 35,  # Limit titles to 35 characters
    'grade'   :  5,  # Longest median grade is 5 characters. Ex: A-~B+
    'workload':  4   # Longest workload is 4 characters: 100%
}
GRADES_TO_VALS = {
    'A+'   : 24,
    'A+~A' : 23,
    'A'    : 22,
    'A~A-' : 21,
    'A-'   : 20,
    'A-~B+': 19,
    'B+'   : 18,
    'B+~B' : 17,
    'B'    : 16,
    'B~B-' : 15,
    'B-'   : 14,
    'B-~C+': 13,
    'C+'   : 12,
    'C+~C' : 11,
    'C'    : 10,
    'C~C-' :  9,
    'C-'   :  8,
    'C-~D+':  7,
    'D+'   :  6,
    'D+~D' :  5,
    'D'    :  4,
    'D~D-' :  3,
    'D-'   :  2,
    'D-~E' :  1,
    'E'    :  0,
    'F'    :  0,
    'P'    :  0
}


class SortMethod(Enum):
    # The integers are the keys you can use on line 21
    NAME     = 1  # Sort by name, i.e. EECS 281
    WORKLOAD = 2  # Sort by workload ascending
    GRADE    = 3  # Sort by grade descending
    TITLE    = 4  # Sort by title, i.e. Data Structures and Algorithms
    ID       = 5  # No sort


class Course:
    def __init__(
        self, id, name, title, grade, display,
        workload, sort_method=SortMethod.ID
        ):
        self.id, self.name, self.display = id, name, display
        self.title = title if title != 'N/A' else None
        self.grade = grade if grade != 'N/A' else None
        # Take off the % sign at the end. Use 101 if N/A
        self.workload = int(workload[:-1]) if workload[-2].isdigit() else 101
        self.sort_key = sort_method
        self.lt_func = self.make_lt_func()
    
    def __str__(self):
        return self.display

    def __lt__(self, other):
        return self.lt_func(self, other)
    
    def make_lt_func(self):
        foo = None

        if self.sort_key == SortMethod.NAME:
            def bar(lhs, rhs):
                return lhs.name < rhs.name
            foo = bar
        
        elif self.sort_key == SortMethod.WORKLOAD:
            def bar(lhs, rhs):
                if not lhs.workload and not rhs.workload:
                    return lhs.id < rhs.id
                if not rhs.workload:
                    return True
                if not lhs.workload:
                    return False
                return lhs.workload < rhs.workload
            foo = bar
        
        elif self.sort_key == SortMethod.GRADE:
            def bar(lhs, rhs):
                if not lhs.grade and not rhs.grade:
                    return lhs.id < rhs.id
                if not rhs.grade:
                    return True
                if not lhs.grade:
                    return False
                return GRADES_TO_VALS[lhs.grade] < GRADES_TO_VALS[rhs.grade]
            foo = bar
        
        elif self.sort_key == SortMethod.TITLE:
            def bar(lhs, rhs):
                if not lhs.title and not rhs.title:
                    return lhs.id < rhs.id
                if not rhs.title:
                    return True
                if not lhs.title:
                    return False
                return lhs.title < rhs.title
            foo = bar
        
        else:
            def bar(lhs, rhs):
                return lhs.id < rhs.id
            foo = bar
        
        return foo


class AtlasRetriever:
    def __init__(self, mode):
        self.redirected = stat.S_ISREG(mode)
        filename = FILE_PATH if FILE_PATH else self.retrieve_filename()
        self.filename = filename[:-4]  # Chop off the .txt
        self.sort_key = SortMethod(
            SORT_METHOD if SORT_METHOD else self.retrieve_sort_method()
        )
        self.driver = webdriver.Chrome(options=self.chrome_options())
    
    def print_newline_if_redirected(self):
        if self.redirected:
            print()

    def retrieve_filename(self):
        while True:
            filename = input('Filename: ')
            self.print_newline_if_redirected()
            if os.path.exists(filename):
                break
        return filename
    
    def retrieve_sort_method(self):
        print('Sorting Methods')
        print('\t1. Name (i.e. EECS 281)')
        print('\t2. Grade Descending')
        print('\t3. Workload Ascending')
        print('\t4. Title (i.e. Data Structrues and Algorithms)')
        print('\t5. No sort')
        while True:
            choice = input('Choice: ')
            if choice.isdigit() and 0 < int(choice) < 6:
                return int(choice)
            print('Invalid choice. Pick a number 1-5')
    
    def chrome_options(self):
        chrome_options = Options()
        chrome_options.binary_location = CHROME_PATH
        chrome_options.add_argument('--headless')
        return chrome_options
    
    def atlas_course_url(self, course_name):
        return f'https://atlas.ai.umich.edu/course/{course_name}'
    
    def click_element(self, element):
        self.driver.find_element(By.XPATH, element).click()
    
    def send_keys_to_element(self, element, keys):
        self.driver.find_element(By.XPATH, element).send_keys(keys)
    
    def get_element_text(self, element):
        return self.driver.find_element(By.XPATH, element).text
    
    def get_element_text_without_error(self, element):
        try:
            text = self.get_element_text(element)
        except NoSuchElementException:
            return 'N/A'
        return text

    def umich_sign_in(self):
        uniqname = UNIQNAME if UNIQNAME else input('Uniqname: ')
        self.print_newline_if_redirected()
        pwd = PASSWORD if PASSWORD else getpass('UMich Password: ')
        self.send_keys_to_element(ELEMENTS['uniqname'], uniqname)
        self.send_keys_to_element(ELEMENTS['password'], pwd)
        self.click_element(ELEMENTS['login_submit'])
        print('Signing into UMich')
        input('Hit enter once finished with Duo 2FA: ')
        time.sleep(5)  # Wait for 2FA to finish
    
    def retrieve_course_data(self, name):
        self.driver.get(self.atlas_course_url(name))
        title = self.get_element_text_without_error(ELEMENTS['title'])
        grade = self.get_element_text_without_error(ELEMENTS['grade'])
        workload = self.get_element_text_without_error(ELEMENTS['workload'])
        print(f'Retrieved {name} data')
        return title, grade, workload
    
    def shorten_course_title(self, title):
        diff = len(title) - DISPLAY_LENGTHS['title']
        return title if diff < 1 else title[:len(title) - diff - 3] + '...'
    
    def make_courses(self):
        courses = []  # Heap
        id = 0
        with open(self.filename + '.txt', 'r', encoding=ENCODING) as fin:
            for line in fin:
                ss = io.StringIO()

                # Ignore comment
                if (line[0] == '#'):
                    continue
                
                name = ' '.join(line.split())  # Remove leading whitespace
                title, grade, workload = self.retrieve_course_data(name)
                title = self.shorten_course_title(title)
                horizontal_align_print(
                    name,
                    DISPLAY_LENGTHS['name'],
                    'right',
                    end=' ',
                    os=ss
                )
                horizontal_align_print(
                    title,
                    DISPLAY_LENGTHS['title'],
                    'left',
                    end=' ',
                    os=ss
                )
                horizontal_align_print(
                    grade,
                    DISPLAY_LENGTHS['grade'],
                    'left',
                    end=' ',
                    os=ss
                )
                horizontal_align_print(
                    workload,
                    DISPLAY_LENGTHS['workload'],
                    'right',
                    os=ss
                )

                heappush(courses, Course(
                    id,
                    name,
                    title,
                    grade,
                    ss.getvalue(),
                    workload,
                    self.sort_key
                ))

                ss.close()
                id += 1
        
        return courses
    
    def print_courses(self, courses):
        with open(self.filename + '-out.txt', 'w', encoding=ENCODING) as fout:
            prev = ''
            while courses:
                course = heappop(courses)
                if course.name != prev:
                    print(course, end='', file=fout)
                prev = course.name
    
    def execute(self):
        self.driver.get(self.atlas_course_url('EECS 281'))
        self.umich_sign_in()
        print('Connected to Atlas.')
        self.print_courses(self.make_courses())
        self.driver.quit()
        print(f'Complete. Output in {self.filename}-out.txt')


def main():
    ar = AtlasRetriever(os.fstat(sys.stdin.fileno()).st_mode)
    ar.execute()


if __name__ == '__main__':
    main()