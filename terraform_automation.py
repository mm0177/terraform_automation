import streamlit as st
import os
from dotenv import load_dotenv
from together import client  # (Unused, can be removed)
load_dotenv()  # Load environment variables from .env file
from together import Together
import json # Used for parsing potential JSON inputs

# --- Configuration ---
# Store your Together API key in Streamlit secrets:
# 1. Create a folder named `.streamlit` in your app's root directory.
# 2. Inside `.streamlit`, create a file named `secrets.toml`.
# 3. Add your API key: `TOGETHER_API_KEY="your_together_api_key_here"`
# 4. Access it in your app using `st.secrets["TOGETHER_API_KEY"]`
# For local testing, you can temporarily hardcode it if you understand the security implications:
# TOGETHER_API_KEY = "your_together_api_key_here" # For local development only, do not commit!


# Initialize Together client
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
together = Together(api_key=TOGETHER_API_KEY)

# --- System Prompt from your instructions ---
SYSTEM_PROMPT = """TERRAFORM CONFIGURATION GENERATOR: OPERATIONAL PROMPT

Role: Expert Terraform configuration generator specialized in AWS modules.

Task: Generate three Terraform files: main.tf, vars.tf, and dev.tfvars, based on a structured module specification provided by the user.

GLOBAL OUTPUT REQUIREMENTS:

File Generation: Always generate both main.tf, vars.tf, and dev.tfvars content.

Code Block Formatting: Each file must be enclosed in a ```terraform` block.

main.tf Module Headers:

#---------------------Beginning of <Module Friendly Name> ------------------------#

#-------------------End of <Module Friendly Name>------------------------------------#

vars.tf Variable Headers:

#<Module Friendly Name> vars

Indentation: All code must use 2 spaces for indentation.

Naming Conventions:

Terraform module names (e.g., s3_bucket) and variable names (e.g., s3_buckets) must be snake_case.

Attribute names within module/variable blocks must match the schema exactly.

RULES FOR main.tf GENERATION:

Module Block Name: <terraform_module_name> from input.

Source Path: ../../../modules/<source_path_suffix> from input.

Conditional Logic by variable_type:

For variable_type: map_of_objects:

Include for_each = var.<variable_name>.

For each attribute listed in module_attributes:

Assign value: each.value.<attribute_name>.

lookup Handling: If attribute includes "use_lookup": true and "lookup_default", use lookup(each.value,"<attribute_name>", <lookup_default_value>). lookup_default_value must be rendered literally (e.g., null, {}, [], "", 0, false).

Special Rule for S3 Buckets (terraform_module_name: s3_bucket):

for_each = { for k, v in var.s3_buckets : k => v if v.create_bucket }

bucket_name = each.key

each.key Assignment: If attribute has "assign_from_each_key": true, set its value to each.key.

For variable_type: single_object:

Do NOT include for_each.

For each attribute listed in module_attributes:

Assign value: var.<variable_name>.<attribute_name>.

lookup Handling: If attribute includes "use_lookup": true and "lookup_default", use lookup(var.<variable_name>,"<attribute_name>", <lookup_default_value>). lookup_default_value must be rendered literally (e.g., null, {}, [], "", 0, false).

Hardcoded Attributes:

If attribute includes "hardcoded_value": <value>, assign that exact value (e.g., enable_prevent_destroy = true). The <value> must be rendered literally (e.g., true, "some_string", 123).

Special Handling for IAM Role (iam) Attributes:

custom_policy_content (when special_handling: file_content_from_path):

custom_policy_content = (
  try(<VAR_SCOPE>.custom_policy_file, null) != null
  ? file(<VAR_SCOPE>.custom_policy_file)
  : null
)

(Note: <VAR_SCOPE> will be each.value for map_of_objects or var.<variable_name> for single_object.)

custom_role_trust_policy (when special_handling: try_file_from_path_if_created_and_not_empty):

custom_role_trust_policy = (
  try(
    <VAR_SCOPE>.create_custom_role_trust_policy && length(<VAR_SCOPE>.custom_role_trust_policy) > 0
      ? file("${path.root}/${<VAR_SCOPE>.custom_role_trust_policy}")
      : "",
    ""
  )
)

(Note: <VAR_SCOPE> will be each.value for map_of_objects or var.<variable_name> for single_object.)

try with List Default:

If attribute has "use_try_list_default": true and a "default_list_value" (e.g., []), use try(<VAR_SCOPE>.<attribute_name>, <default_list_value>). (Again, <VAR_SCOPE> will be each.value or var.<variable_name>.)

RULES FOR vars.tf GENERATION:

Variable Block Name: <variable_name> from input.

Description: <description> from input.

Main Variable type by variable_type:

For variable_type: map_of_objects: map(object({...}))

For variable_type: single_object: object({...})

Inner Attribute Definitions (for each attribute in module_attributes):

type mapping:

type: string -> string

type: number -> number

type: bool -> bool

type: map with value_type: <value_type> -> map(<value_type>)

type: any -> any

List Handling: If list: true -> list(<mapped_type>). E.g., list(string).

Required Attributes: If required: true -> just the <mapped_type>.

Optional Attributes: If optional: true -> optional(<mapped_type>, <default_value>).

If default is provided in the specification, use it.

If default is NOT provided, use: "" for string, 0 for number, false for bool, [] for list, {} for map.

null Default Handling: If default in the specification is explicitly the string "null", use null as the default value (e.g., optional(string, null)).

[NEW CLARIFICATION]: Attribute Definition Requirement: Every attribute explicitly used in the main.tf example for a given module (unless specified as a hardcoded_value) MUST be defined in the module_attributes section of the input specification with its correct type, list, required, and optional properties. This includes attributes used within for_each conditions (e.g., create_bucket for S3).

Special Variables related to special_handling in main.tf:

If special_handling for a different attribute referenced related_variable: "custom_policy_file", then add a separate variable: custom_policy_file = optional(string).

If special_handling for a different attribute referenced related_conditions:

For create_custom_role_trust_policy: create_custom_role_trust_policy = optional(bool, false).

For custom_role_trust_policy: custom_role_trust_policy = optional(string, "").



Attribute Definition Requirement: Every attribute explicitly used in the main.tf example for a given module (unless specified as a hardcoded_value) MUST be defined in the module_attributes section of the input specification with its correct type, list, required, and optional properties. This includes attributes used within for_each conditions (e.g., create_bucket for S3).

RULES FOR dev.tfvars GENERATION:

File Generation: A single dev.tfvars file will be generated for the module.

Code Block Formatting: The file must be enclosed in a ```terraform` block.

File Header: # <Module Friendly Name> dev variables

Indentation: All code must use 2 spaces for indentation.

Variable Assignment:

The main variable (<variable_name>) will be assigned a value.

For variable_type: map_of_objects:

The value will be a map containing one example object.

The key for the example object will be "<module_friendly_name_snake_case>_dev_example".

Inside this object, each attribute from module_attributes will be assigned an example value.

For variable_type: single_object:

The value will be a single object.

Inside this object, each attribute from module_attributes will be assigned an example value.

Example Value Generation (for each attribute):

string type: "example-<attribute_name>" (e.g., "example-function-name").

If attribute_name is name or instance_name or bucket_name or role_name, use "my-<module_friendly_name_snake_case>-dev".

If attribute_name is ami, use "ami-0abcdef1234567890".

If attribute_name is key_name, use "my-ssh-key".

If attribute_name is subnet_id, use "subnet-0abcdef1234567890".

For IAM trusted_role_services use ["lambda.amazonaws.com", "ec2.amazonaws.com"].

For IAM trusted_role_arns use ["arn:aws:iam::123456789012:role/ExampleRole"].

For IAM custom_policy_file or custom_role_trust_policy (path), use "policies/example_policy.json".

For Lambda handler use "index.handler".

For Lambda runtime use "nodejs16.x".

number type: 1 (e.g., timeout = 1).

bool type: true.

For S3 create_bucket, specifically use true.

For create_role or create_custom_role_trust_policy use true.

list(<mapped_type>) type: ["example-item-1", "example-item-2"] (for strings).

For vpc_security_group_ids use ["sg-0abcdef1234567890"].

For custom_policy_arns use ["arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"].

map(<value_type>) type: { "example_key_1" = "example_value_1", "example_key_2" = "example_value_2" }.\n
any type: "example-any-value".

[NEW]: Exclude hardcoded_value from dev.tfvars: Attributes defined with "hardcoded_value" in the main.tf rules must NOT be included in dev.tfvars."""


# --- Streamlit UI ---
st.set_page_config(page_title="Terraform AI Generator", layout="wide")
st.title("Terraform AI Generator for AWS Modules")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Check if the content is code or regular text
        if message["role"] == "assistant" and "```terraform" in message["content"]:
            # Split the content into parts to display text and code separately
            parts = message["content"].split("```terraform")
            for i, part in enumerate(parts):
                if i % 2 == 1: # This is a code block
                    st.code(part.strip(), language="hcl")
                else: # This is regular text
                    st.write(part.strip())
        else:
            st.write(message["content"])

# Accept user input
if prompt := st.chat_input("Provide your module specification (e.g., 'Generate for lambda_functions module'):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Construct the messages for the LLM
            # The system prompt is included once at the beginning of the conversation
            messages_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Append the previous user and assistant messages
            for msg in st.session_state.messages:
                # Exclude previous system messages if any, as we inject it at the start of THIS call
                if msg["role"] != "system":
                    messages_for_llm.append({"role": msg["role"], "content": msg["content"]})


            response = together.chat.completions.create(
                model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                messages=messages_for_llm,
                temperature=0.7, # Adjusted temperature for more consistent code generation
                stream=True,
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            full_response = f"Sorry, I encountered an error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": full_response})
