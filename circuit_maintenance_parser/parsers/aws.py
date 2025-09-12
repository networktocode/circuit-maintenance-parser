"""AWS parser."""

import hashlib
import logging
import quopri
import re

import bs4  # type: ignore
from dateutil import parser

from circuit_maintenance_parser.parser import (
    CircuitImpact,
    EmailSubjectParser,
    Impact,
    Status,
    Text,
)

# pylint: disable=too-many-nested-blocks, too-many-branches

logger = logging.getLogger(__name__)


class SubjectParserAWS1(EmailSubjectParser):
    """Subject parser for AWS notifications."""

    def parse_subject(self, subject):
        """Parse subject.

        Example: AWS Direct Connect Planned Maintenance Notification [AWS Account: 00000001]
        """
        data = {}
        search = re.search(r"\[AWS Account ?I?D?: ([0-9]+)\]", subject)
        if search:
            data["account"] = search.group(1)
        return [data]


class TextParserAWS1(Text):
    """Parse text body of email."""

    @staticmethod
    def get_text_hook(raw):
        """Modify soup before entering `parse_text`."""
        soup = bs4.BeautifulSoup(quopri.decodestring(raw), features="lxml")
        return soup.text

    def parse_plaintext(self, text, data):
        r"""Parse text.

        Example:
            Hello,

            Planned maintenance has been scheduled on an AWS Direct Connect router in A=
            Block, New York, NY from Thu, 20 May 2021 08:00:00 GMT to Thu, 20 Ma=
            y 2021 14:00:00 GMT for 6 hours. During this maintenance window, your AWS D=
            irect Connect services listed below may become unavailable.

            aaaaa-00000001
            aaaaa-00000002
            aaaaa-00000003
            aaaaa-00000004
            aaaaa-00000005
            aaaaa-00000006

            This maintenance is scheduled to avoid disrupting redundant connections at =
            the same time.
        ALTERNATE:
            Planned maintenance has been scheduled on an AWS Direct Connect endpoint in=
            EdgeConnex, Hillsboro, OR. During this maintenance window, your AWS Direct=
            Connect services associated with this event may become unavailable.\n\nThi=
            s maintenance is scheduled to avoid disrupting redundant connections at the=
            same time.\n\nIf you encounter any problems with your connection after the=
            end of this maintenance window, please contact AWS Support(1).\n\n(1) http=
            s://aws.amazon.com/support. For more details, please see https://phd.aws.am=
            azon.com/phd/home?region=3Dus-west-2#/dashboard/open-issues

            Region: us-west-2
            Account Id: 11111111111

            Affected Resources:
            dxvif-fffg1111
            dxcon-fh700000
            dxlag-fh847853
            dxvif-fg000000
            dxvif-f0000000
            dxvif-ffx17y56

            Start Time: Wed, 3 Sep 2025 09:00:00 GMT
            End Time: Wed, 3 Sep 2025 13:00:00 GMT
        """
        impact = Impact.OUTAGE
        for line in text.splitlines():
            if (
                "planned maintenance" in line.lower()
                or "maintenance has been scheduled" in line.lower()
            ):
                data["summary"] = line
            search = re.search(
                r"([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3}) to ([A-Z][a-z]{2}, [0-9]{1,2} [A-Z][a-z]{2,9} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} [A-Z]{2,3})",
                line,
            )
            if search:
                data["start"] = self.dt2ts(parser.parse(search.group(1)))
                data["end"] = self.dt2ts(parser.parse(search.group(2)))
            starttimesearch = re.search(
                r"^Start Time:\s*([A-Za-z]{3}, \d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT)$",
                line,
            )
            endtimesearch = re.search(
                r"^End Time:\s*([A-Za-z]{3}, \d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2} GMT)$",
                line,
            )
            if starttimesearch:
                data["start"] = self.dt2ts(parser.parse(starttimesearch.group(1)))
            if endtimesearch:
                data["end"] = self.dt2ts(parser.parse(endtimesearch.group(1)))
            if "has been cancelled" in line.lower():
                data["status"] = Status.CANCELLED
            if re.match(r"[a-z]{5}-[a-z0-9]{8}", line):
                data["circuits"].append(CircuitImpact(circuit_id=line, impact=impact))
        return data

    def parse_html(self, text, data):
        """Parses AWS HTML notifications.

            Wrapper method to deal with both html and plaintext emails.

        Args:
            text (str): email text.
            data (dict): the dictionary structure started in wrapper method.

        Returns:
            data (dict): dictionary structure with maintenance details
        Example:
            <!doctype html>
            <html xmlns=3D"http://www.w3.org/1999/xhtml" xmlns:v=3D"urn:schemas-microso=
            ft-com:vml" xmlns:o=3D"urn:schemas-microsoft-com:office:office">
            <head>
                <title>
                =20
                </title>
                <!--[if !mso]><!-->
                <meta http-equiv=3D"X-UA-Compatible" content=3D"IE=3Dedge">
                <!--<![endif]-->
                <meta http-equiv=3D"Content-Type" content=3D"text/html; charset=3DUTF-8=
            ">
                <meta name=3D"viewport" content=3D"width=3Ddevice-width, initial-scale=
            =3D1">
                <style type=3D"text/css">
                #outlook a { padding:0; }
                body { margin:0;padding:0;-webkit-text-size-adjust:100%;-ms-text-size=
            -adjust:100%; }
                table, td { border-collapse:collapse;mso-table-lspace:0pt;mso-table-r=
            space:0pt; }
                img { border:0;height:auto;line-height:100%; outline:none;text-decora=
            tion:none;-ms-interpolation-mode:bicubic; }
                p { display:block;margin:13px 0; }
                </style>
                <!--[if mso]>
                <noscript>
                <xml>
                <o:OfficeDocumentSettings>
                <o:AllowPNG/>
                <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
                </xml>
                </noscript>
                <![endif]-->
                <!--[if lte mso 11]>
                <style type=3D"text/css">
                .mj-outlook-group-fix { width:100% !important; }
                </style>
                <![endif]-->
            =20
                <!--[if !mso]><!-->
                    <link href=3D"https://fonts.googleapis.com/css?family=3DUbuntu:300,=
            400,500,700" rel=3D"stylesheet" type=3D"text/css">
                    <style type=3D"text/css">
                    @import url(https://fonts.googleapis.com/css?family=3DUbuntu:300,=
            400,500,700);
                    </style>
                <!--<![endif]-->

            =20
            =20
                <style type=3D"text/css">
                @media only screen and (min-width:480px) {
                    .mj-column-per-100 { width:100% !important; max-width: 100%; }
            .mj-column-per-70 { width:70% !important; max-width: 70%; }
            .mj-column-per-30 { width:30% !important; max-width: 30%; }
            .mj-column-per-50 { width:50% !important; max-width: 50%; }
                }
                </style>
                <style media=3D"screen and (min-width:480px)">
                .moz-text-html .mj-column-per-100 { width:100% !important; max-width:=
            100%; }
            .moz-text-html .mj-column-per-70 { width:70% !important; max-width: 70%; }
            .moz-text-html .mj-column-per-30 { width:30% !important; max-width: 30%; }
            .moz-text-html .mj-column-per-50 { width:50% !important; max-width: 50%; }
                </style>
            =20
            =20
                <style type=3D"text/css">
            =20
            =20

                @media only screen and (max-width:480px) {
                table.mj-full-width-mobile { width: 100% !important; }
                td.mj-full-width-mobile { width: auto !important; }
                }
            =20
                </style>
                <style type=3D"text/css">
            =20
                </style>
            =20
            </head>
            <body style=3D"word-spacing:normal;background-color:#E5E5E5;">
            =20
            =20
                <div
                    style=3D"background-color:#E5E5E5;"
                >
                =20
                =20
                <!--[if mso | IE]><table align=3D"center" border=3D"0" cellpadding=3D=
            "0" cellspacing=3D"0" class=3D"" role=3D"presentation" style=3D"width:600px=
            ;" width=3D"600" ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-h=
            eight-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"margin:0px auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:0 0 20px 0;te=
            xt-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><![endif]-->
                            =20
                <!-- Header -->
                    <!--[if mso | IE]><tr><td class=3D"" width=3D"600px" ><table alig=
            n=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" class=3D"" ro=
            le=3D"presentation" style=3D"width:600px;" width=3D"600" bgcolor=3D"#232F3E=
            " ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-height-rule:exac=
            tly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#232F3E;background-color:#232F3E;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#232F3E;background-color:#232F3=
            E;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:0;text-align:=
            center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"width:600p=
            x;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0;line-height:0;text-align:left;display:inline-block;width:100%;direction=
            :ltr;"
                >
                    <!--[if mso | IE]><table border=3D"0" cellpadding=3D"0" cellspacing=
            =3D"0" role=3D"presentation" ><tr><td style=3D"vertical-align:middle;width:=
            420px;" ><![endif]-->
                        =20
                <div
                    class=3D"mj-column-per-70 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:midd=
            le;width:70%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:middle;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#55575d;"
                ><p style=3D"text-align: left; font-size:25px;color:#fff;">AWS Health=
            Event</p></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                        <!--[if mso | IE]></td><td style=3D"vertical-align:middle;wid=
            th:180px;" ><![endif]-->
                        =20
                <div
                    class=3D"mj-column-per-30 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:midd=
            le;width:30%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:middle;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"right" style=3D"font-size:0px;padding:10px 25px=
            ;word-break:break-word;"
                            >
                            =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"border-collapse:collapse;border-spacing:0px;"
                >
                    <tbody>
                    <tr>
                        <td  style=3D"width:50px;">
                        =20
                <img
                    height=3D"auto" src=3D"https://a0.awsstatic.com/libra-css/images/l=
            ogos/aws_smile-header-desktop-en-white_59x35@2x.png" style=3D"border:0;disp=
            lay:block;outline:none;text-decoration:none;height:auto;width:100%;font-siz=
            e:13px;" width=3D"50"
                />
            =20
                        </td>
                    </tr>
                    </tbody>
                </table>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                        <!--[if mso | IE]></td></tr></table><![endif]-->
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><![endif]-->
                    <!-- Body -->
                    <!--[if mso | IE]><tr><td class=3D"" width=3D"600px" ><table alig=
            n=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" class=3D"" ro=
            le=3D"presentation" style=3D"width:600px;" width=3D"600" bgcolor=3D"#ffffff=
            " ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-height-rule:exac=
            tly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:20px;padding-top:20px;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"vertical-a=
            lign:top;width:600px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top=
            ;width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"right" style=3D"font-size:0px;padding:10px 25px=
            ;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:14px;font-weight:bold;line-height:1;text-align:right;color:#000000;"
                ><a href=3Dhttps://lhrrj7lm.r.us-east-1.awstrack.me/L0/https:%2F%2Fco=
            nsole.aws.amazon.com%2Fnotifications%2Fhome%23%2Fnotifications%2FAWS-Health=
            %2FOperations%2Fa01k43vr7zdhqc4pfztnf2f6ar2%2Fdetails/1/0100019907c54f20-82=
            a2d9c4-36e4-4098-9721-f6725fd3359e-000000/DBCwHaN6YJ8W6Bw65pcXzyav64s=3D441=
            style=3D"color:#545B64">View in Notification Center</a></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:18px;font-weight:bold;line-height:1;text-align:left;color:#000000;"
                >AWS Direct Connect Planned Maintenance Notification [AWS Account: 11=
            1111111111]</div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" vertical-align=3D"middle" style=3D"font-s=
            ize:0px;padding:10px 25px;padding-top:20px;padding-bottom:20px;word-break:b=
            reak-word;"
                            >
                            =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"border-collapse:separate;line-height:100%;"
                >
                    <tbody>
                    <tr>
                        <td
                        align=3D"center" bgcolor=3D"#ff9900" role=3D"presentation" s=
            tyle=3D"border:none;border-radius:3px;cursor:auto;mso-padding-alt:10px 25px=
            ;background:#ff9900;" valign=3D"middle"
                        >
                        <a
                            href=3D"https://lhrrj7lm.r.us-east-1.awstrack.me/L0/https:=
            %2F%2Fhealth.aws.amazon.com%2Fhealth%2Fhome%3Fregion=3Dsa-east-1%23%2Fevent=
            -log%3FeventID=3Darn:aws:health:sa-east-1::event%2FDIRECTCONNECT%2FAWS_DIRE=
            CTCONNECT_MAINTENANCE_SCHEDULED%2FAWS_DIRECTCONNECT_MAINTENANCE_SCHEDULED_8=
            4BDD6BC9D0B29720DC58CBCFB104FBB%26eventTab=3Ddetails%26layout=3Dvertical/1/=
            0100019907c54f20-82a2d9c4-36e4-4098-9721-f6725fd3359e-000000/BlXevSKdpryJl5=
            Ia3mQzXN_b7z0=3D441" style=3D"display:inline-block;background:#ff9900;color=
            :#16191f;font-family:Helvetica, Arial;font-size:14px;font-weight:bold;line-=
            height:120%;margin:0;text-decoration:none;text-transform:none;padding:10px =
            25px;mso-padding-alt:0px;border-radius:3px;" target=3D"_blank"
                        >
                            View details in service console
                        </a>
                        </td>
                    </tr>
                    </tbody>
                </table>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:14px;line-height:22px;text-align:left;color:#000000;"
                ><mj-raw></mj-raw>
                            Hello,
            <br />
            <br />Planned maintenance has been scheduled on an AWS Direct Connect endpo=
            int in Sonda Quilicura, Santiago from Tue, 16 Sep 2025 01:00:00 GMT to Tue,=
            16 Sep 2025 05:00:00 GMT for 4 hours. During this maintenance window, your=
            AWS Direct Connect services listed below may become unavailable.
            <br />
            <br />dxcon-abc12345
            <br />dxvif-1234hfjd
            <br />dxlag-fge1111
            <br />dxcon-ffucore
            <br />dxcon-fg885ug
            <br />
            <br />This maintenance is scheduled to avoid disrupting redundant connectio=
            ns at the same time.
            <br />
            <br />If you encounter any problems with your connection after the end of t=
            his maintenance window, please contact AWS Support[1].
            <br />
            <br />[1] https://aws.amazon.com/support
            <br />
            <br />.
                        <mj-raw></mj-raw></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><![endif]-->
                    <!-- Notification title -->
                    <!--[if mso | IE]><tr><td class=3D"" width=3D"600px" ><table alig=
            n=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" class=3D"" ro=
            le=3D"presentation" style=3D"width:600px;" width=3D"600" bgcolor=3D"#ffffff=
            " ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-height-rule:exac=
            tly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:0;text-align:=
            center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"vertical-a=
            lign:top;width:600px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top=
            ;width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"center" style=3D"font-size:0px;padding:10px 25p=
            x;word-break:break-word;"
                            >
                            =20
                <p
                    style=3D"border-top:solid 1px #D5DBDB;font-size:1px;margin:0px aut=
            o;width:100%;"
                >
                </p>
                =20
                <!--[if mso | IE]><table align=3D"center" border=3D"0" cellpadding=3D=
            "0" cellspacing=3D"0" style=3D"border-top:solid 1px #D5DBDB;font-size:1px;m=
            argin:0px auto;width:550px;" role=3D"presentation" width=3D"550px" ><tr><td=
            style=3D"height:0;line-height:0;"> &nbsp;
            </td></tr></table><![endif]-->
            =20
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:18px;font-weight:bold;line-height:1;text-align:left;color:#000000;"
                >Message metadata</div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><![endif]-->
                =20
                    <!--[if mso | IE]><tr><td class=3D"" width=3D"600px" ><table alig=
            n=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" class=3D"" ro=
            le=3D"presentation" style=3D"width:600px;" width=3D"600" bgcolor=3D"#ffffff=
            " ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-height-rule:exac=
            tly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:10px;padding-top:0;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><![endif]-->
                <!-- Left -->
                    <!--[if mso | IE]><td class=3D"" style=3D"vertical-align:top;widt=
            h:300px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-50 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;=
            width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"border-right:1px solid #D5DBDB;vertical-align:top;" width=3D"=
            100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Affected account</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">111111111111</p></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Event type code</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">AWS_DIRECTCONNECT_MAINTENANCE_SCHEDULED</p></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Event region</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">sa-east-1</p></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">End time</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">Tue, 16 Sep 2025 05:00:00 GMT</p></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td><![endif]-->
                <!-- right -->
                    <!--[if mso | IE]><td class=3D"" style=3D"vertical-align:top;widt=
            h:300px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-50 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;=
            width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Service</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">DIRECTCONNECT</p></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Event type category</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">scheduledChange</p></div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Start time</p>
                                <p style=3D"line-height: 20px; max-width: 250px; word-b=
            reak: break-all;">Tue, 16 Sep 2025 01:00:00 GMT</p></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table><![endif]-->
            =20
            =20
                =20
                <!--[if mso | IE]><table align=3D"center" border=3D"0" cellpadding=3D=
            "0" cellspacing=3D"0" class=3D"" role=3D"presentation" style=3D"width:600px=
            ;" width=3D"600" ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-h=
            eight-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"margin:0px auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:0;text-align:=
            center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" width=3D"600px" ><t=
            able align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" clas=
            s=3D"" role=3D"presentation" style=3D"width:600px;" width=3D"600" bgcolor=
            =3D"#ffffff" ><tr><td style=3D"line-height:0px;font-size:0px;mso-line-heigh=
            t-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:0;padding-top:20px;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"vertical-a=
            lign:top;width:600px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top=
            ;width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:18px;font-weight:bold;line-height:1;text-align:left;color:#000000;"
                >AWS managed notification details</div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:12px;line-height:18px;text-align:left;color:#000000;"
                >AWS Health: Operations events notifications are generated by AWS and=
            sent to selected account contacts. You can add additional delivery channel=
            s for these notifications using <a href=3D"https://lhrrj7lm.r.us-east-1.aws=
            track.me/L0/https:%2F%2Fus-east-1.console.aws.amazon.com%2Fnotifications%2F=
            home%23%2Fmanaged-notifications/1/0100019907c54f20-82a2d9c4-36e4-4098-9721-=
            f6725fd3359e-000000/da6acDecOAC3pa7eOM1rPpedC0s=3D441">AWS managed notifica=
            tions subscriptions</a>.</div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><tr><td class=3D"" widt=
            h=3D"600px" ><table align=3D"center" border=3D"0" cellpadding=3D"0" cellspa=
            cing=3D"0" class=3D"" role=3D"presentation" style=3D"width:600px;" width=3D=
            "600" bgcolor=3D"#ffffff" ><tr><td style=3D"line-height:0px;font-size:0px;m=
            so-line-height-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:0;padding-top:0;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><![endif]-->
                <!-- Left -->
                    <!--[if mso | IE]><td class=3D"" style=3D"vertical-align:top;widt=
            h:300px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-50 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;=
            width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"border-right:1px solid #D5DBDB;vertical-align:top;" width=3D"=
            100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Event type</p>
                            <p style=3D"line-height: 20px; max-width: 250px; word-break=
            : break-all;">AWS Health Event</p></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td><![endif]-->
                <!-- right -->
                    <!--[if mso | IE]><td class=3D"" style=3D"vertical-align:top;widt=
            h:300px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-50 mj-outlook-group-fix" style=3D"font-size=
            :0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top;=
            width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:13px;line-height:1;text-align:left;color:#000000;"
                ><p style=3D"color:#545B64; line-height:0">Category</p>
                            <p style=3D"line-height: 20px; max-width: 250px; word-bre=
            ak: break-all;">Operations</p></div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><tr><td class=3D"" widt=
            h=3D"600px" ><table align=3D"center" border=3D"0" cellpadding=3D"0" cellspa=
            cing=3D"0" class=3D"" role=3D"presentation" style=3D"width:600px;" width=3D=
            "600" bgcolor=3D"#ffffff" ><tr><td style=3D"line-height:0px;font-size:0px;m=
            so-line-height-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"background:#ffffff;background-color:#ffffff;margin:0px=
            auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"background:#ffffff;background-color:#fffff=
            f;width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:20px;padding-top:20px;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"vertical-a=
            lign:top;width:600px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top=
            ;width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"center" style=3D"font-size:0px;padding:10px 25p=
            x;word-break:break-word;"
                            >
                            =20
                <p
                    style=3D"border-top:solid 1px #D5DBDB;font-size:1px;margin:0px aut=
            o;width:100%;"
                >
                </p>
                =20
                <!--[if mso | IE]><table align=3D"center" border=3D"0" cellpadding=3D=
            "0" cellspacing=3D"0" style=3D"border-top:solid 1px #D5DBDB;font-size:1px;m=
            argin:0px auto;width:550px;" role=3D"presentation" width=3D"550px" ><tr><td=
            style=3D"height:0;line-height:0;"> &nbsp;
            </td></tr></table><![endif]-->
            =20
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-bottom:10px;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:14px;line-height:1;text-align:left;color:#000000;"
                >Thank you,</div>
            =20
                            </td>
                        </tr>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            padding-top:0;word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:14px;line-height:1;text-align:left;color:#000000;"
                >Amazon Web Services</div>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr><![endif]-->
                    <!-- Footer -->
                    <!--[if mso | IE]><tr><td class=3D"" width=3D"600px" ><table alig=
            n=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0" class=3D"" ro=
            le=3D"presentation" style=3D"width:600px;" width=3D"600" ><tr><td style=3D"=
            line-height:0px;font-size:0px;mso-line-height-rule:exactly;"><![endif]-->
            =20
                =20
                <div  style=3D"margin:0px auto;max-width:600px;">
                =20
                    <table
                    align=3D"center" border=3D"0" cellpadding=3D"0" cellspacing=3D"0=
            " role=3D"presentation" style=3D"width:100%;"
                    >
                    <tbody>
                        <tr>
                        <td
                            style=3D"direction:ltr;font-size:0px;padding:20px 0;paddin=
            g-bottom:20px;padding-top:20px;text-align:center;"
                        >
                            <!--[if mso | IE]><table role=3D"presentation" border=3D"0"=
            cellpadding=3D"0" cellspacing=3D"0"><tr><td class=3D"" style=3D"vertical-a=
            lign:top;width:600px;" ><![endif]-->
                    =20
                <div
                    class=3D"mj-column-per-100 mj-outlook-group-fix" style=3D"font-siz=
            e:0px;text-align:left;direction:ltr;display:inline-block;vertical-align:top=
            ;width:100%;"
                >
                =20
                <table
                    border=3D"0" cellpadding=3D"0" cellspacing=3D"0" role=3D"presentat=
            ion" style=3D"vertical-align:top;" width=3D"100%"
                >
                    <tbody>
                    =20
                        <tr>
                            <td
                            align=3D"left" style=3D"font-size:0px;padding:10px 25px;=
            word-break:break-word;"
                            >
                            =20
                <div
                    style=3D"font-family:Ubuntu, Helvetica, Arial, sans-serif;font-siz=
            e:12px;line-height:18px;text-align:left;color:#000000;"
                >You are receiving this email because NOTICYEMAIL@COMPANYNAEME.com is sub=
            scribed to <a href=3Dhttps://lhrrj7lm.r.us-east-1.awstrack.me/L0/https:%2F%=
            2Fconsole.aws.amazon.com%2Fnotifications%2Fhome%23%2Fmanaged-notifications%=
            2Fcategory%2FAWS-Health%2Fsub-category%2FOperations%2Fdetails/1/0100019907c=
            54f20-82a2d9c4-36e4-4098-9721-f6725fd3359e-000000/zStVe1KodAmtPfO3ere-Chp9i=
            IE=3D441>AWS Health: Operations events notifications</a>. If you do not wis=
            h to receive emails for these AWS managed notifications, you may <a href=3D=
            "https://lhrrj7lm.r.us-east-1.awstrack.me/L0/https:%2F%2Fus-east-1.console.=
            aws.amazon.com%2Fnotifications%2Fhome%23%2Fmanaged-notifications/2/01000199=
            07c54f20-82a2d9c4-36e4-4098-9721-f6725fd3359e-000000/EXyHN3Yzi4u-A0z7orNkbG=
            DXmVs=3D441">unsubscribe</a>. If you believe you've received this email by =
            error or are experiencing issues managing email subscription, please <a hre=
            f=3D"https://lhrrj7lm.r.us-east-1.awstrack.me/L0/https:%2F%2Faws.amazon.com=
            %2Fcontact-us%2F/1/0100019907c54f20-82a2d9c4-36e4-4098-9721-f6725fd3359e-00=
            0000/8at7TBNQfDG8xKFykYOOEZEVVAY=3D441">contact us</a>.
                    </br></br>
                    Amazon Web Services, Inc. is a subsidiary of Amazon.com, Inc. AMA=
            ZON WEB SERVICES AWS, and related logos are trademarks of Amazon Web Servic=
            es, Inc. or its affiliates.
                    </br></br>
                    This message was produced and distributed by Amazon Web Services,=
            Inc. or its <a href=3D"">affiliates</a> 410 Terry Ave. North, Seattle, WA =
            98109.
                    </br></br>
                    =C2=A9 <mj-raw>2025</mj-raw>, Amazon Web Services, Inc. or its af=
            filiates. All rights reserved. Read our <a href=3D"">Privacy Notice</a>.</d=
            iv>
            =20
                            </td>
                        </tr>
                    =20
                    </tbody>
                </table>
            =20
                </div>
            =20
                    <!--[if mso | IE]></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table></td></tr></table><![endif]-->
                        </td>
                        </tr>
                    </tbody>
                    </table>
                =20
                </div>
            =20
                =20
                <!--[if mso | IE]></td></tr></table><![endif]-->
            =20
            =20
                </div>
            =20
            <img alt=3D"" src=3D"https://lhrrj7lm.r.us-east-1.awstrack.me/I0/01000199=
            07c54f20-82a2d9c4-36e4-4098-9721-f6725fd3359e-000000/wcnjWFcslUssLd1Ed4tt6c=
            0Gov0=3D441" style=3D"display: none; width: 1px; height: 1px;">
            </body>
            </html>
            =20
        """
        impact = Impact.OUTAGE
        soup = bs4.BeautifulSoup(text, "html.parser")
        clean_string = soup.get_text()
        clean_string = re.sub("=20", "", clean_string)
        clean_string = re.sub("=", "", clean_string)
        clean_list = clean_string.splitlines()
        cleaner_list = []
        for line in clean_list:
            newline = line.strip()
            if newline != "":
                cleaner_list.append(newline)
        sumstart = cleaner_list.index("Hello,")
        try:
            sumend = cleaner_list.index("[1] https://aws.amazon.com/support")
        except ValueError:
            sumend = len(cleaner_list)
        newline = " "
        summary = newline.join(cleaner_list[sumstart:sumend])
        if "has been cancelled" in summary.lower():
            data["status"] = Status.CANCELLED
        start_time = cleaner_list[cleaner_list.index("Start time") + 1]
        end_time = cleaner_list[cleaner_list.index("End time") + 1]
        data["start"] = self.dt2ts(parser.parse(start_time))
        data["end"] = self.dt2ts(parser.parse(end_time))
        data["summary"] = summary
        for line in cleaner_list[sumstart:sumend]:
            line = line.strip()
            if re.match(r"[a-z]{5}-[a-z0-9]{8}", line):
                data["circuits"].append(CircuitImpact(circuit_id=line, impact=impact))
        return data

    def parse_text(self, text):
        """Parses AWS notifications.

            Wrapper method to deal with both html and plaintext emails.

        Args:
            text (str): email text.

        Returns:
            data (dict): dictionary structure with maintenance details
        """
        data = {
            "circuits": [],
            "status": Status.CONFIRMED,
        }
        maintenance_id = ""
        if re.search(r"<!doctype html>", text, re.IGNORECASE):
            data = self.parse_html(text, data)
        else:
            data = self.parse_plaintext(text, data)
        # No maintenance ID found in emails, so a hash value is being generated using the start,
        #  end and IDs of all circuits in the notification.
        for circuit in data["circuits"]:
            maintenance_id += circuit.circuit_id
        maintenance_id += str(data["start"])
        maintenance_id += str(data["end"])
        data["maintenance_id"] = hashlib.sha256(
            maintenance_id.encode("utf-8")
        ).hexdigest()  # nosec
        return [data]
