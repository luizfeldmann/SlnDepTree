import re
import os
import argparse
import networkx as nx
import matplotlib.pyplot as plt

class VcProject:
    def __init__(self, name, hash):
        self.name = name
        self.hash = hash
        self.deps = []
        
    def __str__(self):
        return '{} {}:\r\n\t{}'.format(self.name, self.hash, '\r\n\t'.join(self.deps))

# Build the dependency tree from the provided filename
def depTree(filename):
    REGEX_PROJECT = re.compile(r'Project\("\{([^\}]+)\}"\)[\s=]+"([^\"]+)",\s"(.+proj)", "(\{[^\}]+\})"')
    REGEX_SECTION = re.compile(r'\s*ProjectSection\((\w+)\) = postProject')
    REGEX_DEPENDENCY = re.compile(r'\s*(\{[A-Za-z0-9-]+\})\s*=\s*(\{[A-Za-z0-9-]+\})')
    REGEX_END_SECTION = re.compile(r'\s*EndProjectSection')
    REGEX_END_PROJECT = re.compile(r'\s*EndProject')
    
    # Stores the list of all projects
    allProjects = []
    
    # Stores the project being parsed
    currentProject = None
    
    # Stores the name of the section being read
    currentSection = ''
    
    # For each line, match a grammar token
    def parseLine(line):
        nonlocal currentProject
        nonlocal allProjects
        nonlocal currentSection
        
        # If no current project, try to find project start marker
        if currentProject is None:
            if match := REGEX_PROJECT.match(line):
                groups = match.groups()
                currentProject = VcProject(groups[1], groups[3])
        # If there is a current project ...
        else:
            # ... and if we're reading a section ...
            if currentSection:
                # Terminate the current section
                if match := REGEX_END_SECTION.match(line):
                    currentSection = ''
                # List a dependency
                elif currentSection == 'ProjectDependencies':
                    if match := REGEX_DEPENDENCY.match(line):
                        groups = match.groups()
                        dependency = groups[1]
                        currentProject.deps.append(dependency)
            # ... and we're not reading a section ...
            else:
                # find the terminator of current project
                if match := REGEX_END_PROJECT.match(line):
                    allProjects.append(currentProject)
                    currentProject = None
                    
                # find the starter of a section
                elif match := REGEX_SECTION.match(line):
                    groups = match.groups()
                    currentSection = groups[0]
            
    # Open the file and read all lines
    with open(filename, 'rb') as file:
        while line := file.readline().decode('utf-8'):
            parseLine(line)
            
    # Gets name of project with given hash
    def getName(findHash):
        nonlocal allProjects
        return next(proj.name for proj in allProjects if proj.hash == findHash)
        
    # Replace dependency hashes by names
    for proj in allProjects:
        proj.deps = [getName(dep) for dep in proj.deps]
    
    # Print parsed data
    for proj in allProjects: print(proj)
    
    
    # Draw graph
    nodes = [proj.name for proj in allProjects]
    edges = [[proj.name, dep] for proj in allProjects for dep in proj.deps]
    
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    
    pos = nx.spring_layout(G)
    nx.draw_networkx(G, pos, node_shape = "s", node_color = "white")
    
    plt.title(os.path.basename(filename))
    plt.show()
    
# Parse command line arguments
def main():
    parser = argparse.ArgumentParser(description=
    'This script will analyse a Visual Studio\'s solution and build a project dependency tree')

    parser.add_argument('filename')
    
    args = parser.parse_args()
    depTree(args.filename)
    
# Call main() when this is the top-level executing script
if __name__ == "__main__":
    main()