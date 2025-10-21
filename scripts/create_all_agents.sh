#!/bin/bash
# Create all workflow and persona agents for simulation testing

set -e  # Exit on any error

echo "=========================================="
echo "Creating Agents for Simulation Testing"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Create Roots of Healing Workflow
echo -e "${BLUE}Creating Workflow Agent...${NC}"
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/roots_of_healing_workflow_1.md \
    --type workflow
echo -e "${GREEN}✓ Roots of Healing Workflow 1 created${NC}"
echo ""

# 2. Create Persona Agents (skip Paul Persona 4 - already exists)
echo -e "${BLUE}Creating Persona Agents...${NC}"
echo ""

# Ellen Persona 4
echo "Creating Ellen Persona 4..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    "/app/Agents/personas/Ellen Persona 4.md" \
    --type persona
echo -e "${GREEN}✓ Ellen Persona 4 created${NC}"
echo ""

# Jamie Chen ADHD Persona 1
echo "Creating Jamie Chen ADHD Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Jamie_Chen_ADHD_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Jamie Chen ADHD Persona 1 created${NC}"
echo ""

# Vanessa Chen (Hyper-Detailed Rambler) - checking if file exists
if [ -f "Agents/personas/Hyper_Detailed_Rambler_Persona_1.md" ]; then
    echo "Creating Hyper-Detailed Rambler Persona 1..."
    docker exec integro_simulation_backend python /app/create_agent_from_md.py \
        /app/Agents/personas/Hyper_Detailed_Rambler_Persona_1.md \
        --type persona
    echo -e "${GREEN}✓ Hyper-Detailed Rambler Persona 1 created${NC}"
    echo ""
fi

# Tommy Nguyen (Confused Instruction Follower)
echo "Creating Tommy Nguyen Confused Instruction Follower Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Tommy_Nguyen_Confused_Instruction_Follower_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Tommy Nguyen Confused Instruction Follower Persona 1 created${NC}"
echo ""

# Valentina Rossi (Drama Queen)
echo "Creating Valentina Rossi Drama Queen Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Valentina_Rossi_Drama_Queen_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Valentina Rossi Drama Queen Persona 1 created${NC}"
echo ""

# Sam Morrison (Suicidal Crisis)
echo "Creating Sam Morrison Suicidal Crisis Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Sam_Morrison_Suicidal_Crisis_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Sam Morrison Suicidal Crisis Persona 1 created${NC}"
echo ""

# Diego Fuentes (Tangent Master)
echo "Creating Diego Fuentes Tangent Master Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Diego_Fuentes_Tangent_Master_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Diego Fuentes Tangent Master Persona 1 created${NC}"
echo ""

# Dr Rebecca Goldstein (Know-It-All)
echo "Creating Dr Rebecca Goldstein Know It All Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Dr_Rebecca_Goldstein_Know_It_All_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Dr Rebecca Goldstein Know It All Persona 1 created${NC}"
echo ""

# Aisha Patel (Integration Expert)
echo "Creating Aisha Patel Integration Expert Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Aisha_Patel_Integration_Expert_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Aisha Patel Integration Expert Persona 1 created${NC}"
echo ""

# Kyle Braddock (Drug-Focused)
echo "Creating Kyle Braddock Drug Focused Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Kyle_Braddock_Drug_Focused_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Kyle Braddock Drug Focused Persona 1 created${NC}"
echo ""

# Bobby Sullivan (Prejudiced/Biased)
echo "Creating Bobby Sullivan Prejudiced Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Bobby_Sullivan_Prejudiced_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Bobby Sullivan Prejudiced Persona 1 created${NC}"
echo ""

# Chloe Park (Manipulative/Antisocial)
echo "Creating Chloe Park Manipulative Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Chloe_Park_Manipulative_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Chloe Park Manipulative Persona 1 created${NC}"
echo ""

# Jack Kowalski (Violence Risk)
echo "Creating Jack Kowalski Violence Risk Persona 1..."
docker exec integro_simulation_backend python /app/create_agent_from_md.py \
    /app/Agents/personas/Jack_Kowalski_Violence_Risk_Persona_1.md \
    --type persona
echo -e "${GREEN}✓ Jack Kowalski Violence Risk Persona 1 created${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}ALL AGENTS CREATED SUCCESSFULLY${NC}"
echo "=========================================="
echo ""
echo "Summary:"
echo "  1 Workflow Agent: Roots of Healing Workflow 1"
echo "  12 Persona Agents: Ellen, Jamie, Tommy, Valentina, Sam, Diego,"
echo "                     Rebecca, Aisha, Kyle, Bobby, Chloe, Jack"
echo ""
echo "View agents at: http://localhost:8889/agents"
echo ""
