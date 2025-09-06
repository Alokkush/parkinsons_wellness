# app/reports.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import shap

from .model import shap_force_plot_for_row, shap_summary_plot, load_model

# ---------- PDF ----------
def export_pdf(summary_text, plot_images=[], df=None, model=None, scaler=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Parkinson's Wellness Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(summary_text, styles["Normal"]))
    story.append(Spacer(1, 24))

    # Add global SHAP summary plot
    shap_img = shap_summary_plot()
    if shap_img:
        story.append(Paragraph("<b>Global Feature Importance (SHAP)</b>", styles["Heading2"]))
        story.append(Image(io.BytesIO(shap_img), width=400, height=250))
        story.append(Spacer(1, 12))

    # Add patient-specific SHAP plots (if df provided)
    if df is not None and model is not None and scaler is not None and not df.empty:
        X = df.drop(columns=[c for c in ["name", "status"] if c in df.columns], errors="ignore")

        if not X.empty:
            story.append(Paragraph("<b>Patient-Specific Explanations</b>", styles["Heading2"]))
            for row_idx in range(min(3, len(X))):  # only first 3 rows for brevity
                try:
                    fig = shap_force_plot_for_row(model, scaler, X, row_idx)
                    img_bytes = io.BytesIO()
                    fig.savefig(img_bytes, format="png")
                    plt.close(fig)
                    img_bytes.seek(0)
                    story.append(Paragraph(f"Patient {row_idx}", styles["Heading3"]))
                    story.append(Image(img_bytes, width=400, height=200))
                    story.append(Spacer(1, 12))

                    # Top feature contributions table
                    if scaler is not None:
                        X_scaled = scaler.transform(X)
                    else:
                        X_scaled = X.values
                    
                    explainer = shap.Explainer(model, X_scaled)
                    shap_values_row = explainer(X_scaled)[row_idx]

                    contribs = pd.DataFrame({
                        "Feature": X.columns,
                        "Value": X.iloc[row_idx].values,
                        "SHAP_Contribution": shap_values_row.values
                    }).sort_values("SHAP_Contribution", key=abs, ascending=False).head(5)

                    data = [contribs.columns.tolist()] + contribs.values.tolist()
                    table = Table(data, hAlign="LEFT")
                    table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ]))
                    story.append(table)
                    story.append(Spacer(1, 24))
                except Exception as e:
                    story.append(Paragraph(f"Error generating SHAP for patient {row_idx}: {e}", styles["Normal"]))
                    story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# ---------- EXCEL ----------
def export_excel(dataframes: dict, model=None, scaler=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet, index=False)

        # SHAP Global Summary
        shap_img = shap_summary_plot()
        if shap_img:
            try:
                import openpyxl
                from openpyxl.drawing.image import Image as XLImage
                writer.book.create_sheet("SHAP_Global")
                ws = writer.book["SHAP_Global"]
                img_file = io.BytesIO(shap_img)
                img = XLImage(img_file)
                ws.add_image(img, "A1")
            except Exception as e:
                print(f"Error adding SHAP image to Excel: {e}")

        # SHAP Patient-specific (first row only for brevity)
        if "Predictions" in dataframes and not dataframes["Predictions"].empty and model and scaler:
            try:
                df = dataframes["Predictions"]
                X = df.drop(columns=[c for c in ["name", "status"] if c in df.columns], errors="ignore")

                if not X.empty:
                    fig = shap_force_plot_for_row(model, scaler, X, 0)
                    img_bytes = io.BytesIO()
                    fig.savefig(img_bytes, format="png")
                    plt.close(fig)
                    img_bytes.seek(0)

                    writer.book.create_sheet("SHAP_Patient")
                    ws = writer.book["SHAP_Patient"]
                    from openpyxl.drawing.image import Image as XLImage
                    img = XLImage(img_bytes)
                    ws.add_image(img, "A1")
            except Exception as e:
                print(f"Error adding patient SHAP to Excel: {e}")

    return output.getvalue()