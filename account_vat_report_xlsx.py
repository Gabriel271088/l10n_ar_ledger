# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

class AccountVatLedgerXlsx(models.AbstractModel):
    _name = 'report.l10n_ar_ledger.account_vat_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, vat_ledger):
        if vat_ledger.invoice_ids:
            report_name = 'IVA Ventas'
            if vat_ledger.type == 'purchase':
                report_name = 'IVA Compras'

            sheet = workbook.add_worksheet(report_name[:31])
            h = "#"
            money_format = workbook.add_format({'num_format': "$ 0" + h + h + '.' + h + h + ',' + h + h})
            bold = workbook.add_format({'bold': True})
            sheet.write(1, 0, vat_ledger.display_name, bold)

            titles = ['Fecha','Razón Social','CUIT','Responsabilidad AFIP','Tipo de Comprobante','Nro Comprobante','Base imponible','IVA 21','IVA 27','IVA 10.5','Importe Exento / No gravado','IIBB Percepcion','IVA Percepcion','Importe Total']
            for i,title in enumerate(titles):
                sheet.write(3, i, title, bold)


            row = 4
            index = 0
            sheet.set_column('A:F', 30)

            for i,obj in enumerate(vat_ledger.invoice_ids):
                tipocomp = ''
                if obj.l10n_latam_document_type_id.report_name:
                    if 'FACTURA' in obj.l10n_latam_document_type_id.report_name:
                        tipocomp = 'FC'
                        signo = 1
                    elif 'CREDITO' in obj.l10n_latam_document_type_id.report_name:
                        tipocomp = 'NC'
                        signo = -1
                    elif 'DEBITO' in obj.l10n_latam_document_type_id.report_name:
                        tipocomp = 'ND'
                        signo = 1
                    if tipocomp != '':
                        iva_21 = 0
                        iva_27 = 0
                        iva_105 = 0
                        IIBBpercepciones = 0
                        ivapercepcion = 0
                        base_iva0 = 0
                        base_imponible = 0

                sheet.write(row + index, 0, obj.invoice_date.strftime("%Y-%m-%d")) # Fecha
                sheet.write(row + index, 1, obj.partner_id.name) # Razón Social
                if obj.partner_id.vat: # CUIT
                    sheet.write(row + index, 2, obj.partner_id.vat)
                else:
                    sheet.write(row + index, 2, '-')
                sheet.write(row + index, 3, obj.partner_id.l10n_ar_afip_responsibility_type_id.name) # Responsabilidad AFIP
                sheet.write(row + index, 4, obj.l10n_latam_document_type_id.name) # Tipo de Comprobante
                sheet.write(row + index, 5, obj.name) # Nro Comprobante

                # Neto gravado
                netoG = 0
                lineas_invoice = self.env['account.move.line'].search([('move_id', '=', obj.id)])
                for linea in lineas_invoice:
                    if linea['tax_group_id']:
                        taxid = linea['tax_group_id'][0]
                        taxes = self.env['account.tax.group'].search([('id','=', taxid.id)])
                        for tax in taxes:
                            if tax['l10n_ar_vat_afip_code'] == '5':
                                iva_21 += abs(linea['balance']) * signo
                                base_imponible += linea['tax_base_amount'] * signo
                            if tax['l10n_ar_vat_afip_code'] == '6':
                                iva_27 += abs(linea['balance']) * signo
                                base_imponible += linea['tax_base_amount'] * signo
                            if tax['l10n_ar_vat_afip_code'] == '4':
                                iva_105 += abs(linea['balance']) * signo
                                base_imponible += linea['tax_base_amount'] * signo
                            if tax['l10n_ar_tribute_afip_code'] == '07':
                                IIBBpercepciones += linea['balance']
                            if tax['l10n_ar_tribute_afip_code'] == '06':
                                ivapercepcion += linea['balance']
                    else:
                        if linea['l10n_latam_tax_ids'] and (
                                linea['l10n_latam_tax_ids'][0] == 21 or linea['l10n_latam_tax_ids'][0] == 20 or
                                linea['l10n_latam_tax_ids'][0] == 19 or linea['l10n_latam_tax_ids'][0] == 18):
                            base_iva0 += linea['balance']
                if (obj.name[3:4]) == 'C':
                    base_imponible = obj.amount_total * signo
                if base_imponible != 0:
                    sheet.write(row + index, 0, obj.invoice_date.strftime("%d-%m-%Y"))
                    sheet.write(row + index, 1, obj.partner_id.display_name)  # razon social
                    try:
                        sheet.write(row + index, 2, obj.partner_id.vat.replace("-", ""))  # cuit
                    except:
                        sheet.write(row + index, 2, obj.partner_id.vat)
                        #  lo que sigue es codigo de responsabilidad AFIP, no tomo code porque no coincide y no me arriesgo a cambialos en tabla
                    sheet.write(row + index, 3, obj.partner_id.l10n_ar_afip_responsibility_type_id.name)
                    sheet.write(row + index, 4, tipocomp)
                    #sheet.write(row + index, 2, obj.name[3:4])  # letra
                    #sheet.write(row + index, 3, obj.name[5:10])  # punto de venta
                    sheet.write(row + index, 5, obj.name)  # comprobante



                    sheet.write(row + index, 6, base_imponible)
                    sheet.write(row + index, 7, iva_21)  # %iva
                    sheet.write(row + index, 8, iva_27)  # importe iva
                    sheet.write(row + index, 9, iva_105)  # importe iva
                    sheet.write(row + index, 10, base_iva0)  # importe exento
                    sheet.write(row + index, 11, IIBBpercepciones)
                    sheet.write(row + index, 12, ivapercepcion)
                    sheet.write(row + index, 13, abs(obj.amount_total_signed)*signo)  # importe total de la fc, corroborado con manual afip
                    index += 1

