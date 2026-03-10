"""
Export utilities for saved searches.

This module provides functions to export saved searches in various formats
including JSON, Excel, and PDF.
"""

import json
import pandas as pd
from io import BytesIO
from typing import Dict, Any
import streamlit as st


def export_search_json(search_data: Dict[str, Any], entity_name: str) -> bytes:
    """
    Export search data as JSON.

    Args:
        search_data: Complete search data dictionary
        entity_name: Name of the entity

    Returns:
        JSON bytes for download
    """
    # Remove binary data from JSON export
    export_data = search_data.copy()
    if 'results' in export_data and 'pdf_bytes' in export_data['results']:
        export_data['results'] = export_data['results'].copy()
        export_data['results']['pdf_bytes'] = "<binary data excluded from JSON export>"

    json_str = json.dumps(export_data, indent=2, default=str)
    return json_str.encode('utf-8')


def export_search_excel(search_data: Dict[str, Any], entity_name: str) -> BytesIO:
    """
    Export search data as Excel workbook with multiple sheets.

    Args:
        search_data: Complete search data dictionary
        entity_name: Name of the entity

    Returns:
        BytesIO buffer containing Excel file
    """
    output = BytesIO()
    results = search_data.get('results', {})

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_data = {
            'Entity Name': [entity_name],
            'Search Date': [search_data.get('timestamp', '')],
            'Risk Level': [search_data.get('risk_level', 'Unknown')],
            'Match Count': [search_data.get('match_count', 0)],
            'Subsidiary Count': [search_data.get('subsidiary_count', 0)],
            'Sister Count': [search_data.get('sister_count', 0)],
            'Country Filter': [search_data.get('country_filter', 'GLOBAL')],
            'Fuzzy Search': [search_data.get('fuzzy_search', False)],
            'Notes': [search_data.get('notes', '')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Sanctions matches sheet
        us_results = results.get('us_results', [])
        if us_results and 'error' not in us_results[0]:
            sanctions_df = pd.DataFrame(us_results)
            # Limit columns for clarity
            display_cols = ['name', 'type', 'programs', 'Score', 'combined_score', 'addresses']
            available_cols = [col for col in display_cols if col in sanctions_df.columns]
            if available_cols:
                sanctions_df[available_cols].to_excel(writer, sheet_name='Sanctions Matches', index=False)
            else:
                sanctions_df.to_excel(writer, sheet_name='Sanctions Matches', index=False)

        # Media hits sheet
        media_hits = results.get('media_hits', [])
        if media_hits:
            media_df = pd.DataFrame(media_hits)
            media_df.to_excel(writer, sheet_name='Media Coverage', index=False)

        # Conglomerate data
        conglom_data = results.get('conglomerate_data')
        if conglom_data:
            # Subsidiaries sheet
            subsidiaries = conglom_data.get('subsidiaries', [])
            if subsidiaries:
                subs_df = pd.DataFrame(subsidiaries)
                subs_df.to_excel(writer, sheet_name='Subsidiaries', index=False)

            # Sisters sheet
            sisters = conglom_data.get('sisters', [])
            if sisters:
                sisters_df = pd.DataFrame(sisters)
                sisters_df.to_excel(writer, sheet_name='Sister Companies', index=False)

            # Directors sheet
            directors = conglom_data.get('directors', [])
            if directors:
                directors_df = pd.DataFrame(directors)
                directors_df.to_excel(writer, sheet_name='Directors', index=False)

            # Shareholders sheet
            shareholders = conglom_data.get('shareholders', [])
            if shareholders:
                shareholders_df = pd.DataFrame(shareholders)
                shareholders_df.to_excel(writer, sheet_name='Shareholders', index=False)

            # Transactions sheet
            transactions = conglom_data.get('transactions', [])
            if transactions:
                txn_df = pd.DataFrame(transactions)
                txn_df.to_excel(writer, sheet_name='Transactions', index=False)

        # Report sheet
        report = results.get('report', '')
        if report:
            report_data = {'Intelligence Report': [report]}
            report_df = pd.DataFrame(report_data)
            report_df.to_excel(writer, sheet_name='Intelligence Report', index=False)

    output.seek(0)
    return output


def create_download_button_json(search_id: str, search_data: Dict[str, Any], entity_name: str):
    """
    Create Streamlit download button for JSON export.

    Args:
        search_id: Search ID
        search_data: Complete search data
        entity_name: Entity name
    """
    json_bytes = export_search_json(search_data, entity_name)

    st.download_button(
        label="📥 Download JSON",
        data=json_bytes,
        file_name=f"search_{entity_name.replace(' ', '_')}_{search_id[:8]}.json",
        mime="application/json",
        help="Export search data as JSON"
    )


def create_download_button_excel(search_id: str, search_data: Dict[str, Any], entity_name: str):
    """
    Create Streamlit download button for Excel export.

    Args:
        search_id: Search ID
        search_data: Complete search data
        entity_name: Entity name
    """
    excel_buffer = export_search_excel(search_data, entity_name)

    st.download_button(
        label="📥 Download Excel",
        data=excel_buffer.getvalue(),
        file_name=f"search_{entity_name.replace(' ', '_')}_{search_id[:8]}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Export search data as Excel workbook with multiple sheets"
    )


def create_download_button_pdf(search_id: str, search_data: Dict[str, Any], entity_name: str):
    """
    Create Streamlit download button for PDF export.

    Args:
        search_id: Search ID
        search_data: Complete search data
        entity_name: Entity name
    """
    pdf_bytes = search_data.get('results', {}).get('pdf_bytes')

    if pdf_bytes:
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"report_{entity_name.replace(' ', '_')}_{search_id[:8]}.pdf",
            mime="application/pdf",
            help="Download the intelligence report as PDF"
        )
    else:
        st.info("No PDF available for this search")


def create_export_section(search_id: str, search_data: Dict[str, Any], entity_name: str):
    """
    Create a complete export section with all download options.

    Args:
        search_id: Search ID
        search_data: Complete search data
        entity_name: Entity name
    """
    st.markdown("### 📤 Export Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        create_download_button_json(search_id, search_data, entity_name)

    with col2:
        create_download_button_excel(search_id, search_data, entity_name)

    with col3:
        create_download_button_pdf(search_id, search_data, entity_name)
